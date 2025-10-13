```mermaid
flowchart TB
  subgraph Host["Host (Dev machine)"]
    A1["OpenPLC Editor (IDE)"]
    A2["SCADA / Ignition / Node-RED"]
    A3["Modbus Simulator (pyModbus / pymodbus)"]
    A4["GPS Simulator (NMEA → PTY)"]
    A5["MQTT / REST Server (Postgres)"]
    A6["CI / Tests (pytest, Docker)"]
  end

  subgraph Network["Network / Bridge"]
    N1["Modbus TCP"]
    N2["HTTP / MQTT"]
    N3["Serial / PTY Bridges (socat)"]
  end

  subgraph QEMU_OPI["QEMU: OrangePi Zero2 (emulated)"]
    Q1["Linux rootfs"]
    Q2["OpenPLC Runtime"]
    Q3["Serial devices (/dev/ttyS*)"]
    Q4["Modbus Client / Server"]
    Q5["Data Aggregator (GPS filter, encoder)"]
    Q6["Uploader → Remote Server (HTTP/MQTT)"]
  end

  subgraph Peripherals["Virtual Peripherals"]
    P1["Pressure sensor (mA) → Modbus reg"]
    P2["Encoder → Modbus reg / TCP"]
    P3["Actuator / Valve (DO)"]
    P4["GSM modem (AT emu)"]
  end

  %% Connections
  A1 -->|"deploy program"| Q2
  A2 ---|"reads/writes over"| N1
  A3 ---|"Modbus TCP"| N1
  A4 ---|"PTY / socat"| N3
  A5 ---|"HTTP / MQTT"| N2
  A6 -->|"integration tests"| Host

  N1 --> Q4
  N2 --> Q6
  N3 --> Q3

  P1 -->|"simulated values"| A3
  P2 -->|"encoder feedback"| A3
  P3 <--> Q2
  P4 ---|"AT commands over PTY"| Q3

  Q2 -->|"writes telemetry"| Q6
  Q6 -->|"store/log"| A5
  A2 -->|"operator commands"| A1
