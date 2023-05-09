# Clay Gifford 1001918296

import socket
import threading
import sys
import os
import math
import errno
import time
import datetime

# first command line arg is path to config file
CONFIG_PATH = sys.argv[1]
# second is the port to use for connection
ROUTER_PORT = int(sys.argv[2])
# third is the router name
ROUTER_NAME = sys.argv[3]

class Router:
    def __init__(self, port, name):

        # Max size for sending and receiving in bytes
        self.BUFFER_SIZE = 4096

        # maps the router name in config file to the ip address that will be used for it
        self.ROUTER_IP_MAP = {
            'A': '127.0.0.1',
            'B': '127.0.0.2',
            'C': '127.0.0.3',
            'D': '127.0.0.4',
            'E': '127.0.0.5',
            'F': '127.0.0.6'
        }

        # default routing table used for bellman ford algorithm
        self.DEFAULT_ROUTING_TABLE = {
            'A': ('A', math.inf),
            'B': ('B', math.inf),
            'C': ('C', math.inf),
            'D': ('D', math.inf),
            'E': ('E', math.inf),
            'F': ('F', math.inf)
        }

        self.routingTable = {
            'A': ('A', math.inf),
            'B': ('B', math.inf),
            'C': ('C', math.inf),
            'D': ('D', math.inf),
            'E': ('E', math.inf),
            'F': ('F', math.inf)
        }

        self.neighbors = []
        self.neighborTables = {}

        self.ROUTER_PORT = port
        self.ROUTER_NAME = name
        self.NETWORK_SIZE = 6
        self.ROUTER_HOST = self.ROUTER_IP_MAP[name]

        self.server = None

        self.converged = False

        self.shutdown = False

        self.test_case = 1

    # checks for convergence of the router with its neighbors
    # all destinations must have an estimated value that is less than infinity and reachable through a neighboring router
    def check_for_convergence(self):

        for destination in self.routingTable:
            if destination != self.ROUTER_NAME:
                hop, cost = self.routingTable[destination]
                if hop not in self.neighbors or hop not in self.neighborTables:
                    return False
                neighborHop, neighborCost = self.routingTable[hop]
                neighbor_table = self.neighborTables[hop]
                neighborEstimate = neighbor_table[destination]
                if neighbor_table[self.ROUTER_NAME] != neighborCost or neighborCost + neighborEstimate != cost:
                    return False
        return True             


    # read in the config file and update routing table
    # also creates a new default routing table for each neighbor
    def config(self, path):
        self.routingTable[self.ROUTER_NAME] = (self.ROUTER_NAME, 0)

        print(f'\n[NEW CONFIGURATION] configuration set for router {self.ROUTER_NAME} at {self.ROUTER_HOST}:{self.ROUTER_PORT}\n')

        with open(path) as f:
            routes = f.readlines()
            for node in routes:
                name, cost = node.split(",")
                cost = int(cost)
                self.neighbors.append(name)
                self.routingTable[name] = (name, cost)
                print(f'router {name} at {self.ROUTER_IP_MAP[name]}:{self.ROUTER_PORT} has a cost of {cost}')

    # prints the routing table for the current router
    def print_routing_table(self):
        for destination in self.routingTable:
            hop, cost = self.routingTable[destination]
            print(f'router: {self.ROUTER_IP_MAP[destination]}, cost: {cost}')
            #print(f'''router {self.ROUTER_NAME} at {self.ROUTER_HOST} to router {route} at {self.ROUTER_IP_MAP[route]}
            #cost =  {cost}, next hop = router {hop} at {self.ROUTER_IP_MAP[hop]}''')

    # called every time router receives an updated routing table from a neighbor
    def compute_routing_table(self, neighborTable):
        # flag to check if the routing table was changed based on updates from neighbors
        updated = False

        # update the relevant neighbor table, then run bellman ford to recompute 
        # distance vector and broadcast changes, if any

        self.update_neighbor(neighborTable)

        updated = self.bellman_ford()

        if updated:
            self.advertise_dv()
        else:
            print('\n[STATUS] No updates were made to the routing table')

    # constructs the new routing table from the neighbors update
    def update_neighbor(self, update):
        # routing table will be passed between routers in the format destination, hop, cost
        # for each line except the first, which is the name of the neighbor router
        routes = update.splitlines()
        neighbor = routes[0]
        routes = routes[1:]

        table = {}

        # update the neighbor table with new distance vectors
        for route in routes:
            destination, cost = route.split(",")
            if cost == 'infinity':
                cost = math.inf
            else:
                cost = int(cost)
            table[destination] = cost

        self.neighborTables[neighbor] = table

        return neighbor

    # runs the bellman ford algorithm on the neighbor tables to create a new copy of the local routing table
    def bellman_ford(self):
        updated = False

        for neighbor in self.neighborTables:

            table = self.neighborTables[neighbor]

            # self.routingTable[neighbor] = (neighbor, table[self.ROUTER_NAME])

            for destination in table:

                # check if the distance to neighbor plus cost of its distance vector to the destination
                # is less than the current local estimate of distance vector to destination
                # and update accordingly
                cost = table[destination]
                currentHop, currentCost = self.routingTable[destination]
                #neighborHop, neighborDistance = self.routingTable[neighbor]
                neighborDistance = table[self.ROUTER_NAME]

                if not math.isinf(neighborDistance) and neighborDistance + cost < currentCost:

                    if not updated:
                        updated = True
                        print('\n[ROUTING TABLE UPDATED] Effects of update to routing table...') 

                    print(f'destination IP: {self.ROUTER_IP_MAP[destination]}')
                    print(f'current cost: {neighborDistance + cost}')
                    print(f'previous cost: {currentCost}')
                    self.routingTable[destination] = (neighbor, neighborDistance + cost)

        return updated
    
    # formats the data in routing table into plain text to be passed between routers
    def tableToText(self):
        # text to send begins with router name on its own line
        text = self.ROUTER_NAME + '\n'
        # create subsequent lines for each route with router,cost format
        for route in self.routingTable:
            hop, cost = self.routingTable[route]
            if math.isinf(cost):
                cost = 'infinity'
            else:
                cost = str(cost)
            new_info = route + ',' + cost + '\n'
            text += new_info
        
        return text 

    # called every time the router changes its own routing table
    # broadcasts new routing table to neighbors
    def advertise_dv(self):
        # update topology and broadcast any changes to all neighboring routers on the network
        message = self.tableToText()
        message = message.encode()
        for neighbor in self.neighbors:
            try:
                self.server.sendto(message, (self.ROUTER_IP_MAP[neighbor], self.ROUTER_PORT))
            except IOError as e:
                if e.errno == errno.EPIPE:
                    print('\n[BROKEN PIPE] Pipe error bypassed')

    # creates the router
    def start_server(self):
        # Create a UDP server socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print('\n[NEW ROUTER] Router active')
        # serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.settimeout(10)

        # Bind the socket to server address and server ROUTER_PORT
        self.server.bind((self.ROUTER_HOST, self.ROUTER_PORT))

        print(f'[STATUS] Router {self.ROUTER_NAME} bound to {self.ROUTER_HOST} on port {self.ROUTER_PORT}')
        print(f'[CONNECTION DETAILS] Connection Type: UDP')

    # handles incoming information
    def handle_update(self, update):
        update = update.decode()
        self.compute_routing_table(update)

    # handle last broadcast for assignment
    def handle_msg(self, message):
        message = message.decode()
        print(message)
        split_msg = message.splitlines()
        updates_line = split_msg[3]
        num_updates = updates_line.split(':')[1]
        num_updates = int(num_updates)
        
        self.broadcastTC(num_updates + 1)

    # formats the message for the test case
    def format_broadcast(self, num_updates):
        message = f'''Message from router {self.ROUTER_NAME}, at {self.ROUTER_HOST}, on port no. {self.ROUTER_PORT}
        Student ID: 1001918296
        {datetime.datetime.now()}
        Total number of updates: {num_updates}'''
        size = len(message.encode('utf-8'))
        message = message + f'\npayload size: {size} bytes'

        return message.encode()

    # broadcasts the test case to neighboring routers
    def broadcastTC(self, num_updates):
        for neighbor in self.neighbors:
            try:
                if num_updates <= 5:
                    self.server.sendto(self.format_broadcast(num_updates), (self.ROUTER_IP_MAP[neighbor], self.ROUTER_PORT))
                else:
                    self.shutdown = True
            except IOError as e:
                if e.errno == errno.EPIPE:
                    print('\n[BROKEN PIPE] Pipe error bypassed')

    # adds the router to the network 
    def join_network(self):
        self.start_server()
        self.advertise_dv()

        while(not self.shutdown):

            try:
                update, address = self.server.recvfrom(self.BUFFER_SIZE)
                host, port = address
                print(f'\n[NEW UPDATE] Router received update from {host} on UDP port {port}')
                #thread = threading.Thread(target=self.handle_update, args=(update,))
                #thread.start()
                if not self.converged:
                    self.handle_update(update)
                else:
                    self.handle_msg(update)
            except KeyboardInterrupt:
                self.shutdown = True
            except socket.timeout:
                if not self.converged and self.check_for_convergence():
                    self.converged = True
                    print(f'\n[STATUS] CONVERGENCE REACHED')
                    print('\n-----CURRENT ROUTING TABLE-----')
                    self.print_routing_table()
                    time.sleep(5)
                    if self.ROUTER_NAME == 'A':
                        self.broadcastTC(0)

        print('\n[STATUS] Closing connection...')
        self.server.close()
        print('[STATUS] Connection closed.')


if __name__ == '__main__':
    router = Router(ROUTER_PORT, ROUTER_NAME)
    # evaluate router topology from config file
    router.config(CONFIG_PATH)

    router.join_network()