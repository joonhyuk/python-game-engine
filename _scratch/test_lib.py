from __future__ import annotations

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from lib.foundation import *
from config import *
import gc

'''
테스트용 뷰 클래스:

창 열고 기본 루프만 도는...

'''
batch = 100000

start = CLOCK.perf
for i in range(batch):
    a = vectors.zero * i
    if a.length > 0: print('엥?')
print('time1', CLOCK.perf - start)
start = CLOCK.perf

for i in range(batch):
    a = vectors.zero * i
    if a.angle > 0: print('잉?')
print('time2', CLOCK.perf - start)
start = CLOCK.perf

for i in range(batch):
    a = vectors.zero * i
    if a.argument() > 0: print('잉?')
print('time3', CLOCK.perf - start)
start = CLOCK.perf


    
