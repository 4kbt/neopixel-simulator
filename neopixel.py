"""
Drop-in replacement for Adafruit_Neopixel RPI library that simulates the lights.

Example:
    from neopixel import *
    import time

    LED_COUNT = 100
    # All args after the first are ignored, but allowed for compatibility.
    strip = Adafruit_NeoPixel(LED_COUNT)
    # Start the simulation.
    strip.begin()
    i = pi = 0
    while True:
        strip.setPixelColorRGB(pi, 0, 0, 0)
        strip.setPixelColorRGB(i, 255, 255, 255)
        strip.show()

        pi, i = i, (i + 1) % LED_COUNT
        time.sleep(0.1)
"""
import random
import sys
import threading
import wx

class Frame(wx.Frame):
    """UI for simulation."""
    def __init__(self, parent, title, strip):
        self._size = 6
        self._pad = 6
        self._width = 400
        self._height = 200
        self._xjitter = [3 * random.random() for _ in xrange(strip.numPixels())]
        self._yjitter = [4 * random.random() for _ in xrange(strip.numPixels())]

        self._strip = strip

        self._buffer = wx.EmptyBitmap(self._width, self._height)
        self.redraw()
        self._need_resize = False
        self._need_update = False

        wx.Frame.__init__(self, parent, title=title, size=(self._width, self._height))
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Bind(wx.EVT_LEFT_UP, self.onClick)
        self.Bind(wx.EVT_TIMER, self.onTimer)

        self.timer = wx.Timer(self)
        self.timer.Start(1000/60.)

        self.Centre()
        self.Show()

    def center(self, i):
        row_size = (self._width - self._pad) / (2 * self._size + self._pad)
        col = i % row_size
        row = i / row_size

        if row % 2 == 1:
            col = row_size - col - 1

        a = self._pad + self._size
        b = a + self._size
        jx = self._xjitter[i]
        jy = self._yjitter[i]

        return (a + b * col + jx, a + b * row + jy)

    def onPaint(self, e):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self._buffer, 0, 0)

    def onSize(self, e):
        self._need_resize = True

    def resize(self):
        size = self.GetClientSize()
        self._width = size.width
        self._height = size.height
        self._buffer = wx.EmptyBitmap(self._width, self._height)
        self.redraw()

    def redraw(self):
        dc = wx.GCDC(wx.MemoryDC(self._buffer))
        pixels = self._strip.getDisplayed()

        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()

        # Draw string
        for i in xrange(1,len(pixels)):
            x1, y1 = self.center(i-1)
            x2, y2 = self.center(i)
            dc.DrawLine(x1, y1, x2, y2)

        # Draw lights in a second pass so they are on top.
        for i, c in enumerate(pixels):
            dc.SetBrush(wx.Brush(c))
            x, y = self.center(i)
            dc.DrawCircle(x, y, self._size)

    def update(self):
        self._need_update = True

    def onTimer(self, e):

        if self._need_resize:
            self.resize()
            self._need_resize = False

        if self._need_update:
            self.redraw()
            self.Refresh()
            self._need_update = False

    def onClick(self, e):
        wx.App.Get().ExitMainLoop()
        sys.exit()


class Simulation(threading.Thread):
    def __init__(self, strip):
        threading.Thread.__init__(self)
        self._strip = strip
        self._initialized = False

    def run(self):
        self._app = wx.App(clearSigInt=False)
        self._frame = Frame(None, 'Test', strip=self._strip)
        self._initialized = True
        self._app.MainLoop()

    def update(self):
        if not self._initialized:
            return

        self._frame.update()


def Color(red, green, blue, white=0):
    """Packs color values into 32-bit integer."""
    return (white << 24) | (red << 16) | (green << 8) | blue


class Adafruit_NeoPixel(object):
    def __init__(self, num, *args):
        """A simulated neopixel strip.

        Args:
            num: the number of lights in the strip
            *args: the rest of the args are ignored, but allowed for
                compatibility with the neopixel library
        """
        self._buffer = [0] * num
        self._displayed = [wx.Colour(0,0,0)] * num
        self._lock = threading.Lock()

    def begin(self):
        """Starts the simulation."""
        self._sim = Simulation(self)
        self._sim.start()

    def show(self):
        """Updates simulated pixel display."""
        with self._lock:
            self._displayed = [
                wx.Colour((c >> 16) & 0xff,
                          (c >> 8) & 0xff,
                          c & 0xff)
                for c in self._buffer
            ]
        self._sim.update()

    def setPixelColor(self, n, color):
        """Sets color of a given pixel.

        Args:
            n: index of pixel to set
            color: 32-bit packed color value (see Color)

        Raises:
            IndexError if n is out of bounds
        """
        self._buffer[n] = color

    def setPixelColorRGB(self, n, red, green, blue, white=0):
        """Sets RGB color of a given pixel.

        Args:
            n: index of pixel to set
            red: red value (0-255)
            green: green value (0-255)
            blue: blue value (0-255)
            white: white value (0-255, currently unused)

        Raises:
            IndexError if n is out of bounds
        """

        self.setPixelColor(n, Color(red, green, blue, white))

    def getPixels(self):
        """Gets pixel data array for direct manipulation.

        Returns:
            list of 32 bit color values (one per pixel).
        """
        return self._buffer

    def numPixels(self):
        """Gets number of pixels.

        Returns:
            number of pixels
        """
        return len(self._buffer)

    def getPixelColor(self, n):
        """Gets color of a pixel.

        Args:
            n: index of pixel

        Returns:
            32-bit color value for pixel n.
        """
        return self._buffer[n]

    def getDisplayed(self):
        """Gets the array of displayed pixel data.

        Returns:
            List of pixel values at time of last call to show().
        """
        with self._lock:
            return self._displayed

class ws(object):
    """Dummy class for compat. Constants aren't actually used anywhere."""
    SK6812_STRIP_RGBW = 0
    SK6812W_STRIP = 1
