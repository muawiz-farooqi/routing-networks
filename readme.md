Clay Gifford
1001918296
Muhammad Muawiz Farooqi
1001825601

## An application which simulates a router/router protocol using sockets

# Compilation Instructions:

1. navigate to the directory the source code and config files are located in and open a terminal

2. To run the code use: **python <source_code_file> <config_file> <port_no> <router_name>**

## Parameters

**<source_code_file>** - specifies the file to run. Use router.py

**<config_file>** - specifies the .config file to use. Use the one specific to the router you are creating

**<port_no>** - specifies the port number to use. This must be the same accross all routers

**<router_name>** - specifies the router you are creating. Refers to the topology map given in the assignment and is one of [A, B, C, D, E, F]

## Sample Run

To create router A on the CLI, use: **python router.py routerA.config 8000 A**

For router B: **python router.py routerB.config 8000 B**

etc..

