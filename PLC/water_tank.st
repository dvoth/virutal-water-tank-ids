PROGRAM My_Program
  VAR
    high_sensor_pin AT %IX0.3 : BOOL;
    flow_pin AT %QX0.0 : BOOL;
    low_sensor_pin AT %IX0.6 : BOOL;
    pump_pin AT %QX0.1 : BOOL;
  END_VAR

  pump_pin := NOT(NOT(low_sensor_pin));
  pump_pin := low_sensor_pin;
  flow_pin := NOT(high_sensor_pin);
  flow_pin := NOT(high_sensor_pin);
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK TaskMain(INTERVAL := T#5s0ms,PRIORITY := 0);
    PROGRAM Inst0 WITH TaskMain : My_Program;
  END_RESOURCE
END_CONFIGURATION
