# -*- mode: python; coding: utf-8 -*-
def b():
  import pdb, sys
  debugger = pdb.Pdb(stdin=sys.__stdin__, stdout=sys.__stdout__)
  debugger.set_trace(sys._getframe().f_back)
