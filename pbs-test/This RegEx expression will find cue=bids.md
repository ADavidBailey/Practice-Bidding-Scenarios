
Use RegEx 'backreference' to find cue-bids


[1-3][CDHS].([1-4])([DHSC]).\b([2-5])\2.*\b


1C 1H 2H Now is the time for all good men...
1C 1D 2D Pass 3C

1H 1S 2S Pass
1S 2C 3C Pass


([12])(D|H|S|C).*\b([23])\2\b