from jesse.strategies import Strategy, cached
import jesse.indicators as ta
from jesse import utils

'''
Strategy by: RAABOT
Simple EMA crossover strategy. Three EMAs; slow, mid and fast. 
Entry: Fast > Mid > Slow
Filters: (1) Price > Ichimoku span A and B (2) ADX (period=4) > 45
Stop-loss: ATR * Hypterparameter 
Exit: EMA short < EMA long
Position size currently fixed at 5%. Consider more aggressive sizing / hyperparameters / kelly risk / martingale 
'''

class EMA(Strategy):

    def should_long(self) -> bool:
        return self.ema_entry_long and self.ichimoku_filter_long and self.adx_filter

    def should_short(self) -> bool:
        return False

    def should_cancel(self) -> bool:
        return True

    def go_long(self):
        entry = self.price
        stop = self.stop_loss_long(entry)
        qty = self.position_size(entry, stop)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        return False

    def update_position(self):
        qty = self.position.qty
        if self.is_long and self.position.pnl_percentage > 0 and self.ema_exit_long:
            self.take_profit = qty, self.price

    ################################################################
    # # # # # # # # # # stop loss / take profits # # # # # # # # # #
    ################################################################

    def stop_loss_long(self, entry):
        exit = entry - self.stop_atr * self.hp['stop_loss_rate']
        # sometimes an extreme ATR value can lead to a negative price
        if exit <= 0:
            # fallback to donchian channel
            exit = self.dc.lowerband
        return exit

    @property
    def stop_atr(self):
        return ta.atr(self.candles, 14)

    def position_size(self, entry, stop):
        risk_qty = utils.risk_to_qty(self.available_margin, 5, entry, stop, precision=6, fee_rate=self.fee_rate)
        return risk_qty

    ################################################################
    # # # # # # # # # # # # # indicators # # # # # # # # # # # # # #
    ################################################################

    @property
    @cached
    def ema_short(self):
        return ta.ema(self.candles, period=self.hp['ema_short_period'], source_type="close", sequential=False)

    @property
    @cached
    def ema_mid(self):
        return ta.ema(self.candles, period=self.hp['ema_mid_period'], source_type="close", sequential=False)

    @property
    @cached
    def ema_long(self):
        return ta.ema(self.candles, period=self.hp['ema_long_period'], source_type="close", sequential=False)

    @property
    @cached
    def dc(self):
        return ta.donchian(self.candles, period=20)

    @property
    def ichimoku_cloud(self):
        return ta.ichimoku_cloud(self.candles, conversion_line_period=9, base_line_period=26, lagging_line_period=52, displacement=26)

    ################################################################
    # # # # # # # # # #  Entry / Exit Conditions # # # # # # # # # #
    ################################################################

    @property
    def ema_entry_long(self):
        return self.ema_short > self.ema_mid > self.ema_long

    @property
    def ema_exit_long(self):
        return self.ema_short < self.ema_mid

    @property
    def ema_entry_short(self):
        return self.ema_long > self.ema_mid > self.ema_short

    @property
    def ema_exit_short(self):
        return self.price > self.ema_mid

    ################################################################
    # # # # # # # # # # # # # # # Filters # # # # # # # # # # # # #
    ################################################################

    @property
    def ichimoku_filter_long(self):
        span_a = self.ichimoku_cloud[2]
        span_b = self.ichimoku_cloud[3]
        if self.price > span_a and self.price > span_b:
            return True
        return False

    @property
    def adx_filter(self):
        if ta.adx(self.candles, period=4, sequential=False) > 45:
            return True
        return False


    ################################################################
    # # # # # # # # # # # # # Hyperparameters # # # # # # # # # # #
    ################################################################

    def hyperparameters(self):
        return [
            {'name': 'ema_short_period', 'type': int, 'min': 4, 'max': 15, 'default': 8},
            {'name': 'ema_mid_period', 'type': int, 'min': 16, 'max': 30, 'default': 29},
            {'name': 'ema_long_period', 'type': int, 'min': 45, 'max': 70, 'default': 58},
            {'name': 'stop_loss_rate', 'type': float, 'min': 0.8, 'max': 4, 'default': 1.73}
        ]


