import networkx as nx
import random
import osmnx as ox

BETA = .5 # Infection probability
SIGMA = 5 # Number of days someone stays in Exposed state
MU = 15 # Number of days someone stays in Infected State

# Possible states that a node could be in
SUSCEPTIBLE_STATE = "Susceptible"
EXPOSED_STATE = "Exposed"
INFECTED_STATE = "Infected"
REMOVED_STATE = "Removed"

DENSITY_DICT = {
    "Chicago, Illinois, USA": 23.4,
    "Boston, Massachusetts, USA": 24.2,
    "Los Angeles, California, USA": 26.5,
    "New York City, New York, USA": 51.1,
    "Dallas, Texas, USA": 12.2,
    "Miami, Florida, USA": 23.7,
    "Seattle, Washington, USA": 11.3,
    "San Francisco, California, USA": 23.6,
    "Somerville, Massachusetts, USA": 23.7, 
    "Paris, France":20,
    "Berlin, Germany":20,
    "Rome, Italy":20}

class City:
    def __init__(self, location, number_initial_infections, network):
        self.city_name = location
        self.network = network
        self.density = DENSITY_DICT[self.city_name]
        self.beta = BETA
        self.sigma = SIGMA
        self.mu = MU
        self.number_infected = 0
        self.number_exposed = 0
        self.number_removed = 0
        self.init_graph()
        self.network_keys = list(self.network.nodes())
        self.init_infections = number_initial_infections
        self.init_infection(self.init_infections)
        self.color_map = []

    def init_graph(self):
        """Improve the functionality of our graph """
        one_percent_of_nodes = self.network.number_of_nodes() * .01
        num_swaps = round(one_percent_of_nodes * (self.density/10))
        self.network = nx.double_edge_swap(self.network, nswaps=num_swaps)

    def init_infection(self, number_initial_infections):
        """Initially infect a certain number of nodes in a network"""
        nx.set_node_attributes(self.network, SUSCEPTIBLE_STATE, 'state') #Everyone starts succeptible
        nx.set_node_attributes(self.network, float('inf'), 'duration')
        while (self.number_infected < number_initial_infections):
            initial_infect_index = self.network_keys[random.randint(0, len(self.network_keys) - 1)] # get an initial sick node
            self.network.nodes(data=True)[initial_infect_index]['state'] = INFECTED_STATE #infect that node
            self.network.nodes(data=True)[initial_infect_index]['duration'] = self.mu
            self.number_infected += 1
            
    def refresh_city(self):
        self.number_exposed = 0
        self.number_removed = 0
        self.number_infected = 0
        for node_index in self.network_keys: # for every node
            if self.network.nodes[node_index]['state'] != SUSCEPTIBLE_STATE:
                self.network.nodes[node_index]['state'] = SUSCEPTIBLE_STATE
        self.init_infection(self.init_infections)
    
    def run_seir(self, number_of_steps):
        """ Method to run an SEIR Model on the city network for a given number of steps"""
        #loop through infection process 
        for step in range(number_of_steps): #loop through the number of steps
            print("Starting SEIR Time Step: ", step)
            
            for node_index in self.network_keys: # for every node
                if self.network.nodes[node_index]['state'] == INFECTED_STATE: #If that node is infected
                    self.network.nodes[node_index]['duration'] -= 1
                    if (self.network.nodes[node_index]['duration']) == 0:
                        self.network.nodes[node_index]['state'] = REMOVED_STATE
                        self.number_removed += 1
                        self.number_infected -= 1

                    for neighbor in list(self.network.neighbors(node_index)): #Loop through all the neighbors of that node
                        if(random.random() <= self.beta and self.network.nodes[neighbor]['state'] == SUSCEPTIBLE_STATE): # If some random number is greater than beta and the person is not immune then we will infect the neighbor
                            self.network.nodes[neighbor]['state'] = EXPOSED_STATE #infect Neighbor
                            self.network.nodes[neighbor]['duration'] = self.sigma
                            self.number_exposed += 1
                        
                elif self.network.nodes[node_index]['state'] == EXPOSED_STATE:
                     self.network.nodes[node_index]['duration'] -= 1
                     if (self.network.nodes[node_index]['duration']) == 0:
                        self.network.nodes[node_index]['state'] = INFECTED_STATE
                        self.network.nodes[node_index]['duration'] = self.mu + random.randint(-2, 6)
                        self.number_infected += 1

    def run_sd_seir(self, number_of_steps, severity):
        """Method to run an SEIR Model on the city network for a given number of steps during mitigation sequences"""
        #loop through infection process 
        for step in range(number_of_steps): #loop through the number of steps
            print("Starting SEIR Time Step: ", step)
            
            for node_index in self.network_keys: # for every node
                if self.network.nodes[node_index]['state'] == INFECTED_STATE: #If that node is infected
                    self.network.nodes[node_index]['duration'] -= 1
                    if (self.network.nodes[node_index]['duration']) == 0:
                        self.network.nodes[node_index]['state'] = REMOVED_STATE
                        self.number_removed += 1
                        self.number_infected -= 1

                    sd_neighbors = list(self.network.neighbors(node_index))
                    #sd_neighbors = self.select_random(severity, initial_neighbors)
                    for neighbor in sd_neighbors: #Loop through all the neighbors of that node
                        if random.random() > 0.75:
                            if(random.random() <= self.beta/5 and self.network.nodes[neighbor]['state'] == SUSCEPTIBLE_STATE): # If some random number is greater than beta and the person is not immune then we will infect the neighbor
                                self.network.nodes[neighbor]['state'] = EXPOSED_STATE #infect Neighbor
                                self.network.nodes[neighbor]['duration'] = self.sigma
                                self.number_exposed += 1
                elif self.network.nodes[node_index]['state'] == EXPOSED_STATE:
                     self.network.nodes[node_index]['duration'] -= 1
                     if (self.network.nodes[node_index]['duration']) == 0:
                        self.network.nodes[node_index]['state'] = INFECTED_STATE
                        self.network.nodes[node_index]['duration'] = self.mu + random.randint(-2, 6)
                        self.number_infected += 1

    def select_random(self, severity, neighbors):
        included = []
        length = int(len(neighbors)/(severity/1.5))
        for i in range(length):
            num = random.randint(0, len(neighbors) - 1)
            node = neighbors[num]
            if node in included:
                numbers = range(0,num) + range(num + 1, len(neighbors))
                node = neighbors[random.choice(numbers)]
                included.append(node)
        return list(set(included))

    def introduce_infected_node(self):
        """Method to infect a random node"""
        infect_index = random.randint(0, len(self.network_keys) - 1)
        infect_index = self.network_keys[infect_index]
        while (self.network.nodes[infect_index]['state'] != SUSCEPTIBLE_STATE):
            infect_index = self.network_keys[random.randint(0, len(self.network_keys) - 1)]
        self.network.nodes[infect_index]['state'] = EXPOSED_STATE #infect that node
        self.network.nodes[infect_index]['duration'] = self.sigma

        self.number_exposed += 1
