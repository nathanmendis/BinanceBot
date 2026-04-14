import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, FloatPrompt
from typing import Optional
from bot.client import BinanceClient
from bot.orders import OrderManager
from bot.validators import OrderInput, OrderSide, OrderType
from bot.logging_config import logger

app = typer.Typer(help="Binance Futures Testnet Trading Bot")
console = Console()

def display_welcome():
    banner = """
[bold yellow]
*************************************************
*  ____  _                               ____        _  *
* | __ )(_)_ __   __ _ _ __   ___ ___| __ )  ___ | |_ *
* |  _ \\| | '_ \\ / _` | '_ \\ / __/ _ \\  _ \\ / _ \\| __|*
* | |_) | | | | | (_| | | | | (_|  __/ |_) | (_) | |_ *
* |____/|_|_| |_|\\__,_|_| |_|\\___\\___|____/ \\___/ \\__|*
*                                             v1.0  *
*************************************************
[/bold yellow]
"""
    console.print(banner)
    
    features = Table.grid(padding=(0, 2))
    features.add_column(style="cyan bold")
    features.add_column(style="white")
    
    features.add_row("🚀  MARKET", "Immediate execution at current price")
    features.add_row("📉  LIMIT", "Wait for your target price")
    features.add_row("⏳  TWAP", "Automated time-sliced execution")
    features.add_row("📊  GRID", "Dual-order range trading strategy")
    
    console.print(Panel(features, title="Available Capabilities", border_style="blue", expand=False))
    console.print("[dim italic]Tip: Run 'python cli.py --help' to see all command-line options.[/dim italic]")
    console.print()

def run_place_order(
    symbol: Optional[str] = None,
    side: Optional[str] = None,
    order_type: Optional[str] = None,
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    lower_price: Optional[float] = None,
    upper_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    chunks: int = 5,
    interval: int = 10,
):
    """Core logic to place an order, handles prompts if values are missing."""
    try:
        # Manual prompting for missing values
        if not symbol:
            symbol = questionary.text("Enter trading symbol:", default="BTCUSDT").ask()
            
        if not order_type:
            order_type = questionary.select("Select order type:", choices=["MARKET", "LIMIT", "TWAP", "GRID"]).ask()
        
        o_type_upper = order_type.upper()

        if o_type_upper == "GRID":
            if not lower_price:
                lower_price = FloatPrompt.ask("Enter lower price (Buy)")
            if not upper_price:
                upper_price = FloatPrompt.ask("Enter upper price (Sell)")
        else:
            if not side:
                side = questionary.select("Select order side:", choices=["BUY", "SELL"]).ask()
        
        if not quantity:
            quantity = FloatPrompt.ask("Enter quantity")
            
        if o_type_upper == "LIMIT" and not price:
            price = FloatPrompt.ask("Enter limit price")

        # Optional protections for MARKET and LIMIT
        if o_type_upper in ["MARKET", "LIMIT"]:
            add_sl = questionary.confirm("Add Stop Loss?").ask()
            if add_sl:
                stop_loss = FloatPrompt.ask("Enter Stop Loss price")
            
            add_tp = questionary.confirm("Add Take Profit?").ask()
            if add_tp:
                take_profit = FloatPrompt.ask("Enter Take Profit price")

        # Validate input
        order_input = OrderInput(
            symbol=symbol,
            side=side.upper() if side else None,
            order_type=o_type_upper,
            quantity=quantity,
            price=price,
            lower_price=lower_price,
            upper_price=upper_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        console.print(f"\n[yellow]Preparing {order_input.order_type} execution for {order_input.symbol}...[/yellow]")
        
        # Initialize client and manager
        client = BinanceClient()
        manager = OrderManager(client)
        
        response = None
        if order_input.order_type == "MARKET":
            response = manager.place_market_order(
                order_input.symbol, order_input.side, order_input.quantity, 
                order_input.stop_loss, order_input.take_profit
            )
        elif order_input.order_type == "LIMIT":
            response = manager.place_limit_order(
                order_input.symbol, order_input.side, order_input.quantity, order_input.price,
                order_input.stop_loss, order_input.take_profit
            )
        elif order_input.order_type == "TWAP":
            response = manager.place_twap_order(
                order_input.symbol, order_input.side, order_input.quantity,
                chunks=chunks, interval_seconds=interval
            )
        elif order_input.order_type == "GRID":
            response = manager.place_grid_order(order_input.symbol, order_input.quantity, order_input.lower_price, order_input.upper_price)
            
        if response:
            if isinstance(response, list):
                console.print(f"\n[green]Successfully placed all components of the {order_input.order_type}![/green]")
                for i, r in enumerate(response):
                    console.print(f" Order {i+1} ID: {r.get('orderId')} ({r.get('side')} at {r.get('price')})")
            else:
                display_order_success(response)
                
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.error(f"CLI Error: {e}")

@app.command()
def place(
    symbol: Optional[str] = typer.Option(None, help="Trading symbol (e.g. BTCUSDT)"),
    side: Optional[str] = typer.Option(None, help="Order side (BUY/SELL)"),
    order_type: Optional[str] = typer.Option(None, help="Order type (MARKET/LIMIT/TWAP/GRID)"),
    quantity: Optional[float] = typer.Option(None, help="Quantity to trade"),
    price: Optional[float] = typer.Option(None, help="Price for LIMIT orders"),
    lower_price: Optional[float] = typer.Option(None, help="Lower price for GRID orders"),
    upper_price: Optional[float] = typer.Option(None, help="Upper price for GRID orders"),
    stop_loss: Optional[float] = typer.Option(None, help="Stop loss price"),
    take_profit: Optional[float] = typer.Option(None, help="Take profit price"),
    chunks: int = typer.Option(5, help="TWAP: Number of order chunks"),
    interval: int = typer.Option(10, help="TWAP: Seconds between chunks"),
):
    """Place an order on Binance Futures Testnet."""
    run_place_order(symbol, side, order_type, quantity, price, lower_price, upper_price, stop_loss, take_profit, chunks, interval)

def display_order_success(resp):
    table = Table(title="Order Response Details", border_style="green")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    
    fields = ['symbol', 'orderId', 'status', 'type', 'side', 'executedQty', 'avgPrice', 'price']
    for field in fields:
        if field in resp:
            table.add_row(field, str(resp[field]))
            
    console.print(table)
    console.print("[bold green]SUCCESS: Order placed successfully.[/bold green]")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        display_welcome()
        place_now = questionary.confirm("Would you like to place an order?").ask()
        if place_now:
            run_place_order()
        else:
            console.print("Goodbye!")

if __name__ == "__main__":
    app()
