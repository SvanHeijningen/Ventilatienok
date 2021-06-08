
from _pymc_builtins_ import *
from mc.dsa import *
from mc.display import *

import time
import csv

from time import gmtime, strftime

SpGp_NodeId(2)                      # NodeId, wenn das Programm direkt von mPLC, ausgeführt wird.

if not PYMC:
   Sp(0x5000,0, 1)                  # 1=ClearError 3= break MPU program
   print "Hallo"

Sp(0x3004,0, 1)                     # 1=Enable de drive

#--------------------------- Homing
from mc.dsa import *

d = Dsa(2)                                  # NodeId = 2

#init
d.SdoWr(0x3004, 0x00, 0)                  # DEV_Enable - disable
d.SdoWr(0x3003, 0x00, 7)                  # DEV_Mode - POS Mode
d.SdoWr(0x3300, 0x00, 0)                  # VEL_DesiredValue - velocity = 500 [rpm]


# init homing
d.SdoWr(0x3057, 0x00, 0x0135)             # DEV_DinReference
d.SdoWr(0x37B2, 0x00, 22)                 # POS_HomingMethod - methode 22
d.SdoWr(0x37B3 ,0x00, 0)                # POS_HomingOffset
d.SdoWr(0x37B4, 0x00, 1000)                # POS_HomingVelSwitch
d.SdoWr(0x37B4, 0x01, 200)                # POS_HomingVelZero
d.SdoWr(0x37B5, 0x00, 10000)               # POS_HomingAcc
d.SdoWr(0x37B5, 0x01, 10000)              # POS_HomingDec
d.SdoWr(0x37B6, 0x00, 0)              # POS_HomingMaxIndexPath
d.SdoWr(0x37B6, 0x01, 0)                # POS_HomingIndexOffset

d.SdoWr(0x3004, 0x00, 1)                  # DEV_Enable - enable

# last homing state
LastState = -1

while 1:

   act_state = d.SdoRd(0x37B1, 0x02)      # POS_HomingState  - get state
   status = d.SdoRd(0x37B1, 0x00)         # POS_HomingStatus - get status
   error_status = d.SdoRd(0x37B1, 0x01)   # POS_HomingError

   # if idle
   if status == 0:
      d.SdoWr(0x37B0, 0x00, 0x01)         # POS_HomingCmd - start homing

   # only if changed
   if LastState != act_state:
      LastState = act_state

      if   act_state == 0: print "Idle"
      elif act_state == 1: print "Start"
      elif act_state == 2: print "Wait for Ref"
      elif act_state == 3: print "Wait for leave Ref"
      elif act_state == 4: print "Wait for Endswitch negative"
      elif act_state == 5: print "Wait for Endswitch postivie -> negative "
      elif act_state == 6: print "Wait for Endswitch positive"
      elif act_state == 7: print "Wait for Endswitch negative -> positive"
      elif act_state == 8: print "Wait for Index"
      elif act_state == 16: print "Wait for movement finish"
      elif act_state == 32: print "Homing break"
      elif act_state == 33: print "Homing done"
      elif act_state == 34: print "Homing end"

   # homing done
   if (status & 0x10) == 0x10:            # HOMING_STAT_Done
      print "Homing successful"
      print "Distance referenceswitch to index:",
      print d.SdoRd(0x37B1, 0x03)         # POS_HomingRefToIndex
      print "Distance referenceswitch to index in ink:",
      print d.SdoRd(0x37B1, 0x04)         # POS_HomingRefToIndex_cnt
      break                               # end loop

   # error
   if error_status != 0:                  # Error
      print "error: ", error_status
      break                               # end loop

#--------------------------- velocity


Vel = 3000                                     #Velocity

print "Velocity =", d.SdoRd(0x3300, 0x00)      # print the actual value
d.SdoWr(0x3300, 0x00, Vel)                    # new velocity = 1000[rpm]

d.ModeVPos()                              # Operating mode = position controller
d.FctControl(2)                        # activates Fct parameter (Factorgroup)
                                          # It converts the position units
                                          # in [rev]
                                          # (in revolutions of the engine shaft)
d.Enable()                                # enable power stage
d.ActPos(0)                               # Actual position = 0





#----------------------------------------
def AddRowToCSV(filename,data):
   csv_file = csv.writer(open(filename,"ab"), delimiter=';')
   csv_file.writerow(data)

#----------------------------------------
if __name__ == "__main__":
   print "------------"
   data = []
   data.append([time.time()])
   AddRowToCSV(filename="Log_data.csv",data = ["Tijd","Stroom","Snelheid","Positie"])

#----------------------------------------

   Pos = 400

   while(1):
      Positie = Gp(0x3762,0) #ActPos()
      Snelheid = Gp(0x3A04,0) #ActVel()
      MotorStroom = Gp(0x3262,0)  #ActCurr()
      tijd = strftime("%a, %d %b %Y %H:%M:%S", gmtime())
      print tijd,"   Imotor=",MotorStroom, "mA","    Vmotor=",Snelheid, "RPM", "    Positie=",Positie
      AddRowToCSV(filename="Log_data.csv",data = [tijd,MotorStroom,Snelheid,Positie])
      time.sleep(1) # delay sec

      d.Mova(Pos)                             # move to position (absolutly)

      if Pos == Positie:
       Pos = -Pos
