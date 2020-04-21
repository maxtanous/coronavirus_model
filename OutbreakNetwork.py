from opencage.geocoder import OpenCageGeocode
import cartopy.io.shapereader as shpreader
import matplotlib.patches as mpatches
import shapely.geometry as sgeom
import matplotlib.pyplot as plt
from cartopy import geodesic
import cartopy.crs as ccrs
import networkx as nx
from City import City
import osmnx as ox
import shapely
import cartopy
import pickle
import random
import math
import matplotlib as mpl
from copy import deepcopy

mpl.rcParams['figure.dpi'] = 300

# A simulation of the United States coronavirus outbreak using 
# a network model to simulate community spread in cities and 
# transmission through inter-city travel
# credit to: https://scitools.org.uk/cartopy/docs/v0.15/matplotlib/intro.html
# credit to: https://scitools.org.uk/cartopy/docs/v0.15/examples/hurricane_katrina.html
# credit to: 

TOTAL_CASES = []
GEOSCRAPE_DICT = {}
INF_PLOT = {"Boston, Massachusetts, USA": ((9,-3), (9, -5)),
"Dallas, Texas, USA": ((-0.5, -0.5), (0, -2)),
"Chicago, Illinois, USA": ((0, 3.5), (0, 2)),
"Miami, Florida, USA": ((6, 0),(6, -1.5)),
"New York City, New York, USA": ((12, -6), (11, -8)),
"San Francisco, California, USA": ((-2, -2), (-2, -3.5)),
"Seattle, Washington, USA": ((-2, -2), (-2, -3.5)),
"Los Angeles, California, USA": ((-2, -2), (-2, -3.5))}

class OutbreakNetwork:
    """This class bridges City objects by creating edges between Cities that represent the 
    single-day throughput from one city to another via airplane travel. It reads in 
    flight data and creates the City obejcts and their edges. Then it runs a simulated
    outbreak and after any chosen number of steps, implements mitigation measures
    which act to smother the outbreak. The two main mitigation methods are the
    grounding of flights (infected nodes are no longer transmitted from city to 
    city), and social distancing implemented through the SEIR method run in each city. This
    is all plotted against a map of the US, and additionally the growth curve is plotted 
    at the end of the simulation."""
    def __init__(self, input_file, cities):
        # creates an OutbreakNetwork object 
        self.network = nx.DiGraph()
        self.cities = cities
        self.annotations = []
        self.geometries = []
        self.populate_graph(input_file)

    # NETWORK ASSEMBLY
    def populate_graph(self, input_file):
        # populates the graph with cities and flight paths
        file = open(input_file).readlines()
        self.add_edges(file)
    def add_edges(self, file):
        # creates cities and edges
        for edge in file:
            edges = edge.split(" - ")
            city_1 = self.retrieve_city(edges[0])
            city_2 = self.retrieve_city(edges[1])
            self.network.add_weighted_edges_from([(city_1, city_2, edges[2]), (city_2, city_1, edges[3])])
    def retrieve_city(self, name):
        # retrieves a city from the network or creates it if it does not exist
        for city in self.cities:
            print(city.city_name, name)
            if city.city_name == name:
                return city
        print("New city: ", name)
        city = City(name, 1)
        self.cities.append(city)
        self.network.add_node(city)
        print(len(city.network_keys))
        return city

    # SIMULATION FUNCTIONS
    def simulate_travel(self, steps, mitigation_day, fig, ax):
        # simulates travel and transmission of infected nodes between cities
        for i in range(steps):
            print(i)
            if i < mitigation_day:
                figi = str(i) + ".png"
                self.simulate_mobility(0, 0)
                self.travel_step()
                self.plot_infections(ax, i, False)
                plt.savefig(figi)
                self.remove_annotations(fig)
            else:
                figi = str(i) + ".png"
                self.simulate_mobility(0, 2)
                self.mitigation_step()
                self.plot_infections(ax, i, True)
                plt.savefig(figi)
                self.remove_annotations(fig)
    def travel_step(self):
        # simulates a day of travel and city activity
        # the transmission of infected nodes is roughly associated
        # with the ratio of infected nodes to total nodes in the 
        # first city in each edge
        for u, v, weight in self.network.edges(data='weight'):
            if weight is not None:
                threshold = u.number_infected/len(u.network_keys)
                chance = random.random()
                infected_throughput = int((int(weight)/u.density) * threshold)
                print("beta:" + str(infected_throughput))
                if chance < (int(weight) * threshold):
                    v.introduce_infected_node()
                for i in range(infected_throughput):
                    v.introduce_infected_node()
        self.network_seir(0)
    def mitigation_step(self):
        # simulates a day of travel and city activity with lockdown measures in place
        # this means social distancing implemented through an altered SEIR function
        # and the grounding of travel
        self.network_seir(1)
    def network_seir(self, mitigation):
        # iterates through all the cities after network transmission (or lack
        # thereof) and runs them through a step of the SEIR algorithm, with
        # the ability to implement mitgation measures 
        if mitigation == 0:
            for city in self.cities:
                city.run_seir(1)
        else:
            for city in self.cities:
                city.run_sd_seir(1, 2)
    def simulate_mobility(self, mitigation, mitigation_severity):
        # creates random connections to simulate connections/interactions
        # between people who do not live together
        for city in self.cities:
            selection = self.select_random(city.density, city.network_keys)
            selection_two = self.select_random(city.density/2, city.network_keys)
            for node in selection:
                for partner in selection_two:
                    if mitigation == 0:
                        if node != partner:
                            city.network.add_edge(node, partner)
                    else:
                        rand = random.randint(0, mitigation_severity + 1)
                        if rand == mitigation_severity:
                            if node != partner:
                                city.network.add_edge(node, partner)
    def select_random(self, fraction, nodes):
        # helper method
        included = []
        length = int(len(nodes)/fraction)
        for i in range(length):
            num = random.randint(0, len(nodes) - 1)
            node = nodes[num]
            if node in included:
                numbers = range(0,num) + range(num + 1, len(nodes))
                node = nodes[random.choice(numbers)]
                included.append(node)
        return list(set(included))

    # PLOTTING FUNCTIONS
    def plot_cities(self):
        # plots the city names
        for city in self.cities:
            lat, lon = geoscrape(city)
            plot_data = INF_PLOT[city.city_name]
            plot_lon = plot_data[0][0]
            plot_lat = plot_data[0][1]
            plt.text(lon + plot_lon, lat + plot_lat, city.city_name.split(",")[0],
            color ='white', horizontalalignment='right', transform=ccrs.Geodetic())
    def plot_edges(self):
        #plots the flight paths
        for u, v, weight in self.network.edges(data='weight'):
            if weight is not None:
                lat, lon = geoscrape(u)
                lat2, lon2 = geoscrape(v)
                edge = plt.plot([lon, lon2], [lat, lat2], color='red',
                linewidth=1, marker='o',transform=ccrs.Geodetic(),)
    def plot_infections(self, ax, step, mitigation):
        # plots the case numbers in each city
        day = "Day " + str(step)
        if mitigation == True:
            warning = plt.text(-65, 28, "MITIGATION\nPROCEDURES\nUNDERWAY",
            color ='blue', horizontalalignment='right', transform=ccrs.Geodetic())
            self.annotations.append(warning)
        self.plot_city_infections(ax)
        total_cases = plt.text(-120, 26, "Total Cases", color ='white',
        horizontalalignment='right', transform=ccrs.Geodetic())
        total_num = plt.text(-120, 24.2, str(self.count_infected()), color ='red',
        horizontalalignment='right', transform=ccrs.Geodetic())
        current_day = plt.text(-120, 21, day, color ='white',
        horizontalalignment='right', transform=ccrs.Geodetic())
        self.annotations.append(total_cases)
        self.annotations.append(total_num)
        self.annotations.append(current_day)
        TOTAL_CASES.append(self.count_infected())
    def plot_city_infections(self, ax):
        # helper method for plotting city data
        for city in self.cities:
            lat, lon = geoscrape(city)
            inf = str(int(city.number_infected * city.density))
            plot_data = INF_PLOT[city.city_name][1]
            inf_lon = plot_data[0]
            inf_lat = plot_data[1]
            plot = plt.text(lon + inf_lon, lat + inf_lat, inf, color ='red', 
            horizontalalignment='right', transform=ccrs.Geodetic())
            self.plot_infection_circle(ax, lat, lon, city.number_infected)
            self.annotations.append(plot)
    def plot_infection_circle(self, ax, lat, lon, num_inf):
        # plots circles that are scaled in proportion with severity of city outbreak
        circle_points = cartopy.geodesic.Geodesic().circle(lon=lon, lat=lat,
        radius=(math.sqrt(num_inf) * 100 * city.density), endpoint=False)
        geom = shapely.geometry.Polygon(circle_points)
        circ = ax.add_geometries((geom,), crs=cartopy.crs.PlateCarree(),
        facecolor='red', edgecolor='none', linewidth=5)
        self.geometries.append(circ)

    # HELPER METHODS
    def count_infected(self):
        # counts the total number of cases in the network
        num_infected = 0
        for city in self.cities:
            num_infected += city.number_infected * city.density
        return int(num_infected)
    def remove_annotations(self, fig):
        # removes annotations from the figure, a blank slate, if you will
        self.annotations = self.erase(self.annotations)
        self.geometries = self.erase(self.geometries)
        fig.canvas.draw_idle()
    def erase(self, annometries):
        # removal helper method
        for annometry in annometries:
            annometry.remove()
        annometries = []
        return annometries

# OUTER HELPER METHODS
def geoscrape(city):
    # uses geocode to get the coordinates of a given city
    if city.city_name in GEOSCRAPE_DICT:
        return GEOSCRAPE_DICT[city.city_name]
    else:
        key = "b031396d90cd418c91b5d1e968e5c59c"
        geocoder = OpenCageGeocode(key)
        query = city.city_name
        results = geocoder.geocode(query)
        lat = results[0]['geometry']['lat']
        lng = results[0]['geometry']['lng']
        GEOSCRAPE_DICT[city.city_name] = lat, lng
        return lat, lng
def initialze_plot():
    fig = plt.figure()
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.LambertConformal())
    ax.stock_img()
    ax.set_extent([-130, -66.5, 20, 50], ccrs.Geodetic())
    shapename = 'admin_1_states_provinces_lakes_shp'
    states_shp = shpreader.natural_earth(resolution='110m', category='cultural', name=shapename)
    plt.title('Coronavirus Network Model, United States')
    for state in shpreader.Reader(states_shp).geometries():
        facecolor = 'black'
        edgecolor = 'dimgrey'
        ax.add_geometries([state], ccrs.PlateCarree(), facecolor=facecolor, edgecolor=edgecolor)
    return fig, ax
    
# MAIN METHOD
def main():
    cities = []
    US = OutbreakNetwork("FlightCapacities.txt", cities)
    # plots the network against a backdrop of the United States
    fig, ax = initialze_plot()
    US.plot_edges()
    US.plot_cities()
    US.simulate_travel(100, 60, fig, ax)
    figure_2 = plt.figure()
    plt.plot(TOTAL_CASES)
    plt.ylabel('# of ')
    plt.savefig("Total Cases.png")
    plt.show()

main()
