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

# A simulation of the United States coronavirus outbreak using 
# a network model to simulate community spread in cities and 
# transmission through an inter-city travel network
# credit to: https://scitools.org.uk/cartopy/docs/v0.15/matplotlib/intro.html
# credit to: https://scitools.org.uk/cartopy/docs/v0.15/examples/hurricane_katrina.html

class UnitedStates:
    def __init__(self, input_file):
        self.network = nx.DiGraph()
        self.cities = []
        self.annotations = []
        self.geometries = []
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
        city = City(name, 5)
        self.cities.append(city)
        self.network.add_node(city)
        return city
    def simulate_travel(self, steps, fig, ax):
        # simulates travel and transmission of infected nodes between cities
        for i in range(steps):
            figi = str(i) + ".png"
            self.travel_step()
            self.plot_infections(ax)
            plt.savefig(figi)
            self.remove_annotations(fig)
    def travel_step(self):
        # simulates a day of travel and city activity
        for u, v, weight in self.network.edges(data='weight'):
            if weight is not None:
                beta = int(int(weight) * (u.number_infected/len(u.network_keys)))
                for i in range(beta + 1):
                    v.introduce_infected_node()
            v.run_seir(1)
    def plot_cities(self):
        # plots the city names
        for city in self.cities:
            lat, lon = geoscrape(city)
            plt.text(lon - 2 , lat - 2, city.city_name.split(",")[0], color ='white', horizontalalignment='right', transform=ccrs.Geodetic())
    def plot_edges(self):
        #plots the flight paths
        for u, v, weight in self.network.edges(data='weight'):
            if weight is not None:
                lat, lon = geoscrape(u)
                lat2, lon2 = geoscrape(v)
                plt.plot([lon, lon2], [lat, lat2], color='red', linewidth=2, marker='o',transform=ccrs.Geodetic(),)
            pass
    def plot_infections(self, ax):
        # plots the case numbers in each city
        for city in self.cities:
            lat, lon = geoscrape(city)
            plot = plt.text(lon - 2 , lat - 3.5, str(city.number_infected), color ='red', horizontalalignment='right', transform=ccrs.Geodetic())
            self.plot_infection_circle(ax, lat, lon, city.number_infected)
            self.annotations.append(plot)
        total_cases = plt.text(-120, 26, "Total Cases", color ='white', horizontalalignment='right', transform=ccrs.Geodetic())
        total = plt.text(-120, 24.2, str(self.count_infected()), color ='red', horizontalalignment='right', transform=ccrs.Geodetic())
        self.annotations.append(total_cases)
        self.annotations.append(total)
    def plot_infection_circle(self, ax, lat, lon, num_inf):
        # plots circles that are scaled in proportion with severity of city outbreak
        circle_points = cartopy.geodesic.Geodesic().circle(lon=lon, lat=lat, radius=(math.log(num_inf) * 250), endpoint=False)
        geom = shapely.geometry.Polygon(circle_points)
        circ = ax.add_geometries((geom,), crs=cartopy.crs.PlateCarree(), facecolor='red', edgecolor='none', linewidth=5)
        self.geometries.append(circ)
    def count_infected(self):
        # counts the total number of cases in the network
        num_infected = 0
        for city in self.cities:
            num_infected += city.number_infected
        return num_infected
    def remove_annotations(self, fig):
        # removes annotations from the figure, a blank slate, if you will
        for artist in self.annotations:
            artist.remove()
        self.annotations = []
        for artist in self.geometries:
            artist.remove()
        self.geometries = []
        fig.canvas.draw_idle()

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
def main():
    US = UnitedStates("FlightCapacities.txt")
    # plots the network against a backdrop of the United States
    fig, ax = initialze_plot()
    US.plot_edges()
    US.plot_cities()
    US.simulate_travel(20, fig, ax)
    US.plot_infections(ax)
    plt.show()

main()
