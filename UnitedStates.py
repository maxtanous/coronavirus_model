from City import City
import networkx as nx
import matplotlib.pyplot as plt
import osmnx as ox
import pickle
from opencage.geocoder import OpenCageGeocode
import matplotlib.patches as mpatches
import shapely.geometry as sgeom
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import random

# A simulation of the United States coronavirus outbreak using 
# a network model both to simulate community spread in cities and 
# transmission through an inter-city travel network
# credit to: https://scitools.org.uk/cartopy/docs/v0.15/matplotlib/intro.html
# credit to: https://scitools.org.uk/cartopy/docs/v0.15/examples/hurricane_katrina.html

class UnitedStates:
    def __init__(self, input_file):
        self.network = nx.DiGraph()
        self.cities = []
        self.number_infected = 0
        self.populate_graph(input_file)
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
        city = City(name, 10)
        self.cities.append(city)
        self.network.add_node(city)
        return city
    def simulate_travel(self, steps):
        # simulates travel and transmission of infected nodes between cities
        for i in range(steps):
            self.travel_step()
    def travel_step(self):
        # simulates a day of travel and city activity
        for u, v, weight in self.network.edges(data='weight'):
            if weight is not None:
                beta = int(weight * (u.number_infected/len(u.network_keys)))
                for i in range(beta + 1):
                    v.introduce_infected_node()
            v.run_seir(1)
        #self.plot_infections()
    def plot_cities(self):
        # plots the city names
        for city in self.cities:
            lat, lon = geoscrape(city)
            plt.text(lon - 2 , lat - 2, city.city_name.split(",")[0], color ='white', horizontalalignment='right', transform=ccrs.Geodetic())
    def plot_infections(self):
        # plots the case numbers in each city
        for city in self.cities:
            lat, lon = geoscrape(city)
            plt.text(lon - 2 , lat - 3, str(city.number_infected), color ='white', horizontalalignment='right', transform=ccrs.Geodetic())
    def plot_edges(self):
        #plots the flight paths
        for u, v, weight in self.network.edges(data='weight'):
            if weight is not None:
                lat, lon = geoscrape(u)
                lat2, lon2 = geoscrape(v)
                plt.plot([lon, lon2], [lat, lat2], color='blue', linewidth=2, marker='o',transform=ccrs.Geodetic(),)
            pass
def geoscrape(city):
    # uses geocode to get the coordinates of a given city
    key = "b031396d90cd418c91b5d1e968e5c59c"
    geocoder = OpenCageGeocode(key)
    query = city.city_name
    results = geocoder.geocode(query)
    lat = results[0]['geometry']['lat']
    lng = results[0]['geometry']['lng']
    return lat, lng
def initialze_plot():
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.LambertConformal())
    ax.stock_img()
    ax.set_extent([-130, -66.5, 20, 50], ccrs.Geodetic())
    shapename = 'admin_1_states_provinces_lakes_shp'
    states_shp = shpreader.natural_earth(resolution='110m', category='cultural', name=shapename)
    plt.title('Airport Network of Major US Cities')
    for state in shpreader.Reader(states_shp).geometries():
        facecolor = 'black'
        edgecolor = 'white'
        ax.add_geometries([state], ccrs.PlateCarree(), facecolor=facecolor, edgecolor=edgecolor)
def main():
    US = UnitedStates("FlightCapacities.txt")
    # plots the network against a backdrop of the United States
    initialze_plot()
    US.plot_edges()
    US.plot_cities()
    US.simulate_travel(15)
    US.plot_infections()
    plt.show()

main()
