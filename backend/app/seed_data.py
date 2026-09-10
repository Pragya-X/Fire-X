"""Static India-focused reference geography + hotspot generation for seed data.

Everything is deterministic (``random.Random(42)``) so the demo is repeatable.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from shapely.geometry import LineString, Point, Polygon

from app.gis.engine import SpatialDataset

SEED = 42

# --------------------------------------------------------------------------
# States with centroid + sample districts
# --------------------------------------------------------------------------
STATES: dict[str, dict[str, Any]] = {
    "Punjab": {"lat": 30.79, "lon": 75.84, "districts": ["Ludhiana", "Amritsar", "Bathinda", "Patiala", "Jalandhar"]},
    "Haryana": {"lat": 29.06, "lon": 76.08, "districts": ["Panipat", "Gurugram", "Hisar", "Karnal", "Faridabad"]},
    "Rajasthan": {"lat": 27.02, "lon": 74.22, "districts": ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Alwar", "Udaipur"]},
    "Gujarat": {"lat": 22.26, "lon": 71.19, "districts": ["Jamnagar", "Surat", "Vadodara", "Bharuch", "Rajkot", "Ahmedabad"]},
    "Maharashtra": {"lat": 19.75, "lon": 75.71, "districts": ["Nagpur", "Pune", "Aurangabad", "Nashik", "Mumbai", "Amravati"]},
    "Odisha": {"lat": 20.95, "lon": 85.09, "districts": ["Angul", "Sundargarh", "Kandhamal", "Balasore", "Mayurbhanj"]},
    "Assam": {"lat": 26.20, "lon": 92.94, "districts": ["Kamrup", "Golaghat", "Tinsukia", "Dibrugarh", "Nagaon"]},
    "Madhya Pradesh": {"lat": 23.47, "lon": 77.42, "districts": ["Singrauli", "Hoshangabad", "Balaghat", "Seoni", "Jabalpur", "Chhindwara"]},
    "Uttar Pradesh": {"lat": 27.39, "lon": 79.56, "districts": ["Mathura", "Lucknow", "Varanasi", "Bareilly", "Kanpur", "Gorakhpur"]},
    "West Bengal": {"lat": 23.08, "lon": 87.65, "districts": ["Paschim Bardhaman", "Bankura", "Jalpaiguri", "Purulia", "Maldah"]},
    "Jharkhand": {"lat": 23.61, "lon": 85.28, "districts": ["Dhanbad", "Bokaro", "West Singhbhum", "Hazaribagh", "Palamu"]},
    "Chhattisgarh": {"lat": 21.28, "lon": 81.63, "districts": ["Korba", "Raipur", "Bastar", "Surguja", "Dantewada", "Kanker"]},
    "Telangana": {"lat": 18.11, "lon": 79.02, "districts": ["Hyderabad", "Warangal", "Nizamabad", "Adilabad"]},
    "Karnataka": {"lat": 15.32, "lon": 75.71, "districts": ["Chikkamagaluru", "Uttara Kannada", "Kodagu", "Mysuru", "Ballari"]},
    "Tamil Nadu": {"lat": 11.13, "lon": 78.66, "districts": ["Nilgiris", "Coimbatore", "Vellore", "Dindigul", "Chennai"]},
    "Andhra Pradesh": {"lat": 15.91, "lon": 79.74, "districts": ["Visakhapatnam", "Chittoor", "Kurnool", "Prakasam"]},
    "Bihar": {"lat": 25.84, "lon": 85.85, "districts": ["Begusarai", "Patna", "Gaya", "Muzaffarpur", "Bhagalpur"]},
    "Kerala": {"lat": 10.16, "lon": 76.43, "districts": ["Ernakulam", "Palakkad", "Idukki", "Wayanad", "Thrissur"]},
}

# --------------------------------------------------------------------------
# Cities (name, state, lat, lon) - used for settlements and road/rail spurs
# --------------------------------------------------------------------------
CITIES: list[tuple[str, str, float, float]] = [
    ("Amritsar", "Punjab", 31.63, 74.87), ("Ludhiana", "Punjab", 30.90, 75.85),
    ("Jalandhar", "Punjab", 31.33, 75.58), ("Patiala", "Punjab", 30.34, 76.39),
    ("Bathinda", "Punjab", 30.21, 74.94), ("Mohali", "Punjab", 30.70, 76.72),
    ("Gurugram", "Haryana", 28.46, 77.03), ("Faridabad", "Haryana", 28.41, 77.31),
    ("Panipat", "Haryana", 29.39, 76.96), ("Karnal", "Haryana", 29.69, 76.98),
    ("Hisar", "Haryana", 29.15, 75.72), ("Rohtak", "Haryana", 28.90, 76.57),
    ("Jaipur", "Rajasthan", 26.91, 75.79), ("Jodhpur", "Rajasthan", 26.24, 73.02),
    ("Udaipur", "Rajasthan", 24.59, 73.71), ("Kota", "Rajasthan", 25.21, 75.86),
    ("Bikaner", "Rajasthan", 28.02, 73.31), ("Ajmer", "Rajasthan", 26.45, 74.64),
    ("Alwar", "Rajasthan", 27.55, 76.61), ("Bharatpur", "Rajasthan", 27.22, 77.49),
    ("Ahmedabad", "Gujarat", 23.02, 72.57), ("Surat", "Gujarat", 21.17, 72.83),
    ("Vadodara", "Gujarat", 22.31, 73.18), ("Rajkot", "Gujarat", 22.30, 70.80),
    ("Jamnagar", "Gujarat", 22.47, 70.06), ("Gandhinagar", "Gujarat", 23.22, 72.65),
    ("Bharuch", "Gujarat", 21.71, 72.99), ("Bhavnagar", "Gujarat", 21.76, 72.15),
    ("Mumbai", "Maharashtra", 19.08, 72.88), ("Pune", "Maharashtra", 18.52, 73.86),
    ("Nagpur", "Maharashtra", 21.15, 79.09), ("Nashik", "Maharashtra", 19.99, 73.79),
    ("Aurangabad", "Maharashtra", 19.88, 75.34), ("Solapur", "Maharashtra", 17.66, 75.91),
    ("Kolhapur", "Maharashtra", 16.70, 74.24), ("Thane", "Maharashtra", 19.22, 72.98),
    ("Amravati", "Maharashtra", 20.93, 77.75),
    ("Bhubaneswar", "Odisha", 20.30, 85.82), ("Cuttack", "Odisha", 20.46, 85.88),
    ("Rourkela", "Odisha", 22.26, 84.85), ("Sambalpur", "Odisha", 21.47, 83.97),
    ("Berhampur", "Odisha", 19.31, 84.79), ("Balasore", "Odisha", 21.49, 86.93),
    ("Guwahati", "Assam", 26.14, 91.74), ("Dibrugarh", "Assam", 27.47, 94.91),
    ("Silchar", "Assam", 24.83, 92.78), ("Jorhat", "Assam", 26.75, 94.22),
    ("Tezpur", "Assam", 26.63, 92.80),
    ("Bhopal", "Madhya Pradesh", 23.26, 77.41), ("Indore", "Madhya Pradesh", 22.72, 75.86),
    ("Jabalpur", "Madhya Pradesh", 23.18, 79.99), ("Gwalior", "Madhya Pradesh", 26.22, 78.18),
    ("Ujjain", "Madhya Pradesh", 23.18, 75.78), ("Sagar", "Madhya Pradesh", 23.84, 78.74),
    ("Singrauli", "Madhya Pradesh", 24.20, 82.66), ("Rewa", "Madhya Pradesh", 24.53, 81.30),
    ("Lucknow", "Uttar Pradesh", 26.85, 80.95), ("Kanpur", "Uttar Pradesh", 26.45, 80.33),
    ("Varanasi", "Uttar Pradesh", 25.32, 82.99), ("Agra", "Uttar Pradesh", 27.18, 78.01),
    ("Meerut", "Uttar Pradesh", 28.98, 77.71), ("Mathura", "Uttar Pradesh", 27.49, 77.67),
    ("Prayagraj", "Uttar Pradesh", 25.44, 81.85), ("Ghaziabad", "Uttar Pradesh", 28.67, 77.42),
    ("Bareilly", "Uttar Pradesh", 28.37, 79.43),
    ("Kolkata", "West Bengal", 22.57, 88.36), ("Howrah", "West Bengal", 22.60, 88.31),
    ("Durgapur", "West Bengal", 23.55, 87.31), ("Asansol", "West Bengal", 23.68, 86.98),
    ("Siliguri", "West Bengal", 26.73, 88.42), ("Bardhaman", "West Bengal", 23.24, 87.86),
    ("Haldia", "West Bengal", 22.06, 88.11),
    ("Ranchi", "Jharkhand", 23.34, 85.31), ("Jamshedpur", "Jharkhand", 22.80, 86.18),
    ("Dhanbad", "Jharkhand", 23.80, 86.43), ("Bokaro", "Jharkhand", 23.67, 86.15),
    ("Hazaribagh", "Jharkhand", 23.99, 85.36),
    ("Raipur", "Chhattisgarh", 21.25, 81.63), ("Bhilai", "Chhattisgarh", 21.19, 81.31),
    ("Bilaspur", "Chhattisgarh", 22.08, 82.15), ("Korba", "Chhattisgarh", 22.35, 82.68),
    ("Jagdalpur", "Chhattisgarh", 19.07, 82.03),
    ("Hyderabad", "Telangana", 17.39, 78.49), ("Warangal", "Telangana", 18.00, 79.59),
    ("Karimnagar", "Telangana", 18.44, 79.13), ("Nizamabad", "Telangana", 18.67, 78.10),
    ("Bengaluru", "Karnataka", 12.97, 77.59), ("Mysuru", "Karnataka", 12.30, 76.64),
    ("Hubballi", "Karnataka", 15.36, 75.12), ("Mangaluru", "Karnataka", 12.91, 74.86),
    ("Belagavi", "Karnataka", 15.85, 74.50), ("Davanagere", "Karnataka", 14.47, 75.92),
    ("Chennai", "Tamil Nadu", 13.08, 80.27), ("Coimbatore", "Tamil Nadu", 11.02, 76.96),
    ("Madurai", "Tamil Nadu", 9.93, 78.12), ("Tiruchirappalli", "Tamil Nadu", 10.79, 78.70),
    ("Salem", "Tamil Nadu", 11.66, 78.15), ("Tiruppur", "Tamil Nadu", 11.11, 77.34),
    ("Visakhapatnam", "Andhra Pradesh", 17.69, 83.22), ("Vijayawada", "Andhra Pradesh", 16.51, 80.65),
    ("Guntur", "Andhra Pradesh", 16.31, 80.44), ("Nellore", "Andhra Pradesh", 14.44, 79.99),
    ("Tirupati", "Andhra Pradesh", 13.63, 79.42),
    ("Patna", "Bihar", 25.59, 85.14), ("Gaya", "Bihar", 24.79, 85.00),
    ("Muzaffarpur", "Bihar", 26.12, 85.39), ("Bhagalpur", "Bihar", 25.24, 86.98),
    ("Begusarai", "Bihar", 25.42, 86.13),
    ("Thiruvananthapuram", "Kerala", 8.52, 76.94), ("Kochi", "Kerala", 9.93, 76.27),
    ("Kozhikode", "Kerala", 11.26, 75.78), ("Thrissur", "Kerala", 10.53, 76.21),
]

# --------------------------------------------------------------------------
# Forests (name, state, lat, lon, radius_km)
# --------------------------------------------------------------------------
FORESTS: list[tuple[str, str, float, float, float]] = [
    ("Gir National Park", "Gujarat", 21.13, 70.78, 35.0),
    ("Simlipal National Park", "Odisha", 21.75, 86.35, 30.0),
    ("Sundarbans", "West Bengal", 21.95, 88.89, 25.0),
    ("Kaziranga National Park", "Assam", 26.58, 93.17, 20.0),
    ("Manas National Park", "Assam", 26.75, 90.95, 20.0),
    ("Nameri National Park", "Assam", 26.93, 92.89, 15.0),
    ("Dibru-Saikhowa", "Assam", 27.67, 95.37, 15.0),
    ("Tadoba Andhari", "Maharashtra", 20.25, 79.40, 20.0),
    ("Melghat Tiger Reserve", "Maharashtra", 21.45, 77.20, 25.0),
    ("Pench Tiger Reserve", "Madhya Pradesh", 21.67, 79.25, 25.0),
    ("Kanha National Park", "Madhya Pradesh", 22.30, 80.60, 25.0),
    ("Bandhavgarh National Park", "Madhya Pradesh", 23.70, 81.00, 20.0),
    ("Satpura Tiger Reserve", "Madhya Pradesh", 22.42, 78.20, 25.0),
    ("Sanjay-Dubri Reserve", "Madhya Pradesh", 23.60, 82.30, 20.0),
    ("Palamau Tiger Reserve", "Jharkhand", 23.88, 84.20, 25.0),
    ("Dalma Wildlife Sanctuary", "Jharkhand", 22.83, 86.25, 15.0),
    ("Saranda Forest", "Jharkhand", 22.30, 85.25, 25.0),
    ("Kanger Valley", "Chhattisgarh", 19.03, 81.95, 20.0),
    ("Achanakmar Reserve", "Chhattisgarh", 22.30, 81.90, 20.0),
    ("Indravati National Park", "Chhattisgarh", 19.20, 81.30, 25.0),
    ("Bhoramdeo Sanctuary", "Chhattisgarh", 21.95, 81.40, 15.0),
    ("Rajaji National Park", "Uttarakhand", 30.05, 78.20, 20.0),
    ("Jim Corbett National Park", "Uttarakhand", 29.53, 78.77, 20.0),
    ("Sariska Tiger Reserve", "Rajasthan", 27.32, 76.43, 25.0),
    ("Ranthambore National Park", "Rajasthan", 26.02, 76.50, 25.0),
    ("Kumbhalgarh Sanctuary", "Rajasthan", 25.15, 73.58, 20.0),
    ("Mukurthi National Park", "Tamil Nadu", 11.36, 76.60, 12.0),
    ("Silent Valley", "Kerala", 11.14, 76.47, 12.0),
    ("Nagarhole National Park", "Karnataka", 11.83, 76.18, 20.0),
    ("Bandipur National Park", "Karnataka", 11.66, 76.63, 20.0),
    ("Bhadra Sanctuary", "Karnataka", 13.44, 75.50, 15.0),
    ("Amrabad Tiger Reserve", "Telangana", 16.35, 78.90, 25.0),
    ("Kawal Tiger Reserve", "Telangana", 19.10, 79.00, 20.0),
    ("Bor Tiger Reserve", "Maharashtra", 21.10, 78.70, 15.0),
    ("Sanjay Gandhi NP", "Maharashtra", 19.22, 72.93, 10.0),
    ("Dandeli Wildlife", "Karnataka", 15.23, 74.65, 15.0),
    ("Mudumalai National Park", "Tamil Nadu", 11.58, 76.55, 15.0),
    ("Bhitarkanika", "Odisha", 20.65, 86.87, 15.0),
]

# --------------------------------------------------------------------------
# Industrial zones (code, name, type, lat, lon, state, district)
# --------------------------------------------------------------------------
INDUSTRIAL_ZONES: list[tuple[str, str, str, float, float, str, str]] = [
    ("ZN-01", "Jamnagar Refinery Complex", "Refinery", 22.2598, 69.7854, "Gujarat", "Jamnagar"),
    ("ZN-02", "Panipat Refinery", "Refinery", 29.3996, 76.9600, "Haryana", "Panipat"),
    ("ZN-03", "Barauni Refinery", "Refinery", 25.3700, 86.2400, "Bihar", "Begusarai"),
    ("ZN-04", "Mathura Refinery", "Refinery", 27.4900, 77.6800, "Uttar Pradesh", "Mathura"),
    ("ZN-05", "Visakhapatnam Refinery", "Refinery", 17.7200, 83.3000, "Andhra Pradesh", "Visakhapatnam"),
    ("ZN-06", "Kochi Refinery", "Refinery", 10.0600, 76.2400, "Kerala", "Ernakulam"),
    ("ZN-07", "Manali Refinery Chennai", "Refinery", 13.1700, 80.3000, "Tamil Nadu", "Chennai"),
    ("ZN-08", "Bathinda Refinery", "Refinery", 30.1500, 74.8700, "Punjab", "Bathinda"),
    ("ZN-09", "Guwahati Refinery", "Refinery", 26.1600, 91.7700, "Assam", "Kamrup"),
    ("ZN-10", "Numaligarh Refinery", "Refinery", 26.6300, 93.8600, "Assam", "Golaghat"),
    ("ZN-11", "Digboi Refinery", "Refinery", 27.3800, 95.6200, "Assam", "Tinsukia"),
    ("ZN-12", "Rourkela Steel Plant", "Factory", 22.2600, 84.8800, "Odisha", "Sundargarh"),
    ("ZN-13", "Bokaro Steel Plant", "Factory", 23.6700, 86.1500, "Jharkhand", "Bokaro"),
    ("ZN-14", "Durgapur Steel Plant", "Factory", 23.5500, 87.3200, "West Bengal", "Paschim Bardhaman"),
    ("ZN-15", "Singrauli Thermal Complex", "Power Plant", 24.0500, 82.6000, "Madhya Pradesh", "Singrauli"),
    ("ZN-16", "Korba Thermal Complex", "Power Plant", 22.3500, 82.6800, "Chhattisgarh", "Korba"),
    ("ZN-17", "Talcher Thermal Complex", "Power Plant", 20.9500, 85.2100, "Odisha", "Angul"),
    ("ZN-18", "Jharia Coalfield", "Mine", 23.7500, 86.4200, "Jharkhand", "Dhanbad"),
    ("ZN-19", "Raniganj Coalfield", "Mine", 23.6200, 87.1200, "West Bengal", "Paschim Bardhaman"),
    ("ZN-20", "Korba Coalfield", "Mine", 22.4300, 82.4800, "Chhattisgarh", "Korba"),
    ("ZN-21", "Gandhar Petrochemical", "Factory", 21.7500, 73.0600, "Gujarat", "Bharuch"),
    ("ZN-22", "Mumbai Refinery & Petrochem", "Refinery", 19.0000, 72.9000, "Maharashtra", "Mumbai"),
    ("ZN-23", "Raipur Industrial Belt", "Industrial Park", 21.2500, 81.6300, "Chhattisgarh", "Raipur"),
    ("ZN-24", "Ludhiana Industrial Belt", "Industrial Park", 30.9000, 75.8500, "Punjab", "Ludhiana"),
    ("ZN-25", "Nagpur MIDC", "Industrial Park", 21.1458, 79.0882, "Maharashtra", "Nagpur"),
    ("ZN-26", "Haldia Petrochemicals", "Factory", 22.0500, 88.1300, "West Bengal", "Purba Medinipur"),
]

# Extra standalone assets beyond zones (code, name, type, lat, lon, state, district)
REFINERIES: list[tuple[str, str, float, float, str, str]] = [
    ("RF-01", "Haldia Refinery", 22.0500, 88.1300, "West Bengal", "Purba Medinipur"),
    ("RF-02", "Paradip Refinery", 20.2700, 86.6700, "Odisha", "Jagatsinghpur"),
    ("RF-03", "Vadinar Refinery", 22.4800, 69.7200, "Gujarat", "Devbhumi Dwarka"),
]

FACTORIES: list[tuple[str, str, float, float, str, str]] = [
    ("FC-01", "Bhilai Steel Plant", 21.1900, 81.3000, "Chhattisgarh", "Durg"),
    ("FC-02", "Tata Steel Jamshedpur", 22.7900, 86.1800, "Jharkhand", "East Singhbhum"),
    ("FC-03", "JSW Vijayanagar Steel", 15.2500, 76.4200, "Karnataka", "Ballari"),
    ("FC-04", "Vedanta Jharsuguda", 21.8500, 84.0300, "Odisha", "Jharsuguda"),
    ("FC-05", "NALCO Angul", 20.8400, 85.0900, "Odisha", "Angul"),
    ("FC-06", "Hindalco Renukoot", 24.1300, 83.0200, "Uttar Pradesh", "Sonbhadra"),
    ("FC-07", "Tata Motors Pune", 18.6400, 73.7600, "Maharashtra", "Pune"),
    ("FC-08", "Maruti Suzuki Gurugram", 28.4500, 77.0300, "Haryana", "Gurugram"),
    ("FC-09", "Hero MotoCorp Faridabad", 28.4100, 77.3100, "Haryana", "Faridabad"),
    ("FC-10", "ACC Kymore Cement", 24.1300, 81.2300, "Madhya Pradesh", "Katni"),
    ("FC-11", "UltraTech Reddipalayam", 12.0600, 79.8200, "Tamil Nadu", "Villupuram"),
    ("FC-12", "Surat Textile Hub", 21.1700, 72.8300, "Gujarat", "Surat"),
    ("FC-13", "Tiruppur Knitwear Cluster", 11.1100, 77.3400, "Tamil Nadu", "Tiruppur"),
    ("FC-14", "Hyderabad Pharma City", 17.4500, 78.3700, "Telangana", "Hyderabad"),
    ("FC-15", "Vizag Pharma SEZ", 17.7200, 83.2200, "Andhra Pradesh", "Visakhapatnam"),
    ("FC-16", "Sriperumbudur Electronics", 12.9700, 79.9900, "Tamil Nadu", "Kanchipuram"),
    ("FC-17", "Noida Electronics SEZ", 28.5700, 77.3200, "Uttar Pradesh", "Gautam Buddha Nagar"),
    ("FC-18", "Jagdishpur Paper Mill", 26.5200, 80.9800, "Uttar Pradesh", "Amethi"),
    ("FC-19", "Burnpur IISCO Steel", 23.6600, 86.9400, "West Bengal", "Paschim Bardhaman"),
    ("FC-20", "Hirakud Aluminium", 21.5200, 83.9500, "Odisha", "Sambalpur"),
    ("FC-21", "Bhusawal Thermal Ancillary", 21.0500, 75.7700, "Maharashtra", "Buldhana"),
    ("FC-22", "Kanpur Leather Cluster", 26.4500, 80.3300, "Uttar Pradesh", "Kanpur"),
    ("FC-23", "Rajpura Industrial Estate", 30.4800, 76.5900, "Punjab", "Patiala"),
    ("FC-24", "Bahadurgarh Industrial Area", 28.6900, 76.9300, "Haryana", "Jhajjar"),
    ("FC-25", "Dewas Industrial Area", 22.9600, 76.0600, "Madhya Pradesh", "Dewas"),
    ("FC-26", "Pithampur Industrial Area", 22.6600, 75.8300, "Madhya Pradesh", "Dhar"),
    ("FC-27", "Bhuj Cement Works", 23.2500, 69.6700, "Gujarat", "Kutch"),
    ("FC-28", "Ankleshwar GIDC", 21.6200, 73.0100, "Gujarat", "Bharuch"),
    ("FC-29", "Sri City SEZ", 13.5300, 79.9700, "Andhra Pradesh", "Tirupati"),
    ("FC-30", "Ambattur Industrial Estate", 13.1100, 80.1600, "Tamil Nadu", "Chennai"),
]

POWER_PLANTS: list[tuple[str, str, float, float, str, str]] = [
    ("PP-01", "Vindhyachal Super Thermal", 24.1000, 82.6700, "Madhya Pradesh", "Singrauli"),
    ("PP-02", "Sasan Ultra Mega Power", 24.1900, 82.5900, "Madhya Pradesh", "Singrauli"),
    ("PP-03", "Kahalgaon Super Thermal", 25.2700, 87.2700, "Bihar", "Bhagalpur"),
    ("PP-04", "Farakka Super Thermal", 24.7800, 87.9000, "West Bengal", "Murshidabad"),
    ("PP-05", "Rihand Super Thermal", 24.0300, 82.8000, "Uttar Pradesh", "Sonbhadra"),
    ("PP-06", "NTPC Dadri", 28.5800, 77.6100, "Uttar Pradesh", "Gautam Buddha Nagar"),
    ("PP-07", "Badarpur Thermal", 28.5100, 77.2900, "Delhi", "New Delhi"),
    ("PP-08", "Mundra Ultra Mega Power", 22.8300, 69.5500, "Gujarat", "Kutch"),
    ("PP-09", "Kawas Gas Power", 21.1000, 72.6500, "Gujarat", "Surat"),
    ("PP-10", "Hazira Gas Power", 21.1300, 72.6600, "Gujarat", "Surat"),
    ("PP-11", "Ennore Thermal", 13.2200, 80.3200, "Tamil Nadu", "Chennai"),
    ("PP-12", "Tuticorin Thermal", 8.7900, 78.1700, "Tamil Nadu", "Thoothukudi"),
    ("PP-13", "Chandrapur Thermal", 19.9300, 79.3000, "Maharashtra", "Chandrapur"),
    ("PP-14", "Parichha Thermal", 25.5200, 78.7500, "Uttar Pradesh", "Jhansi"),
    ("PP-15", "Barh Super Thermal", 25.4700, 85.7200, "Bihar", "Patna"),
]

MINES: list[tuple[str, str, float, float, str, str]] = [
    ("MN-01", "Kudremukh Iron Ore", 13.2000, 75.2000, "Karnataka", "Chikkamagaluru"),
    ("MN-02", "Bailadila Iron Ore", 18.6600, 81.2000, "Chhattisgarh", "Dantewada"),
    ("MN-03", "Kiriburu Iron Ore", 22.1100, 85.2700, "Jharkhand", "West Singhbhum"),
    ("MN-04", "Malanjkhand Copper", 22.0300, 80.7100, "Madhya Pradesh", "Balaghat"),
    ("MN-05", "Kolar Gold Fields", 12.9600, 78.2700, "Karnataka", "Kolar"),
    ("MN-06", "Hutti Gold Mine", 16.1900, 76.6600, "Karnataka", "Raichur"),
    ("MN-07", "Neyveli Lignite", 11.5300, 79.4800, "Tamil Nadu", "Cuddalore"),
    ("MN-08", "Barsuan Iron Ore", 21.8700, 84.8700, "Odisha", "Sundargarh"),
    ("MN-09", "Bolani Iron Ore", 22.0800, 85.3700, "Odisha", "Kendujhar"),
    ("MN-10", "Rampura-Agucha Zinc", 25.8300, 74.2200, "Rajasthan", "Bhilwara"),
    ("MN-11", "Gevra Open Cast Coal", 22.4000, 82.4000, "Chhattisgarh", "Korba"),
    ("MN-12", "North Karanpura Coal", 23.9600, 85.5400, "Jharkhand", "Hazaribagh"),
    ("MN-13", "Talcher Coal Field", 20.9500, 85.2100, "Odisha", "Angul"),
    ("MN-14", "Makrana Marble", 27.0400, 74.7200, "Rajasthan", "Nagaur"),
    ("MN-15", "Jaduguda Uranium", 22.6600, 86.3400, "Jharkhand", "East Singhbhum"),
]

# --------------------------------------------------------------------------
# Pipelines (name, list of (lat, lon) waypoints)
# --------------------------------------------------------------------------
PIPELINES: list[tuple[str, list[tuple[float, float]]]] = [
    ("JGPL Jamnagar-Delhi", [(22.47, 69.79), (26.91, 75.79), (28.61, 77.21)]),
    ("Mundra-Delhi Crude", [(22.83, 69.55), (26.91, 75.79), (28.61, 77.21)]),
    ("Paradip-Haldia", [(20.27, 86.67), (22.06, 88.11)]),
    ("Haldia-Barauni Crude", [(22.06, 88.11), (25.37, 86.24)]),
    ("Kandla-Bathinda", [(23.03, 70.22), (29.0, 74.0), (30.21, 74.94)]),
    ("Numaligarh-Siliguri", [(26.63, 93.86), (26.73, 88.42)]),
    ("Mumbai-Nagpur HPCL", [(19.08, 72.88), (21.15, 79.09)]),
    ("Visakhapatnam-Hyderabad", [(17.69, 83.22), (17.39, 78.49)]),
    ("Kochi-Karur", [(9.93, 76.27), (10.95, 78.07)]),
    ("Panipat-Jalandhar", [(29.40, 76.96), (31.33, 75.58)]),
    ("Mathura-Agra", [(27.49, 77.68), (27.18, 78.01)]),
    ("Korba-Raipur Coal Slurry", [(22.35, 82.68), (21.25, 81.63)]),
]

# --------------------------------------------------------------------------
# National road / railway corridors (name, list of (lat, lon))
# --------------------------------------------------------------------------
HIGHWAYS: list[tuple[str, list[tuple[float, float]]]] = [
    ("NH-48 Delhi-Mumbai", [(28.61, 77.21), (26.91, 75.79), (23.02, 72.57), (19.08, 72.88)]),
    ("NH-19 Delhi-Kolkata", [(28.61, 77.21), (27.18, 78.01), (25.59, 85.14), (23.55, 87.31), (22.57, 88.36)]),
    ("NH-44 Delhi-Chennai", [(28.61, 77.21), (25.59, 85.14), (21.25, 81.63), (17.39, 78.49), (13.08, 80.27)]),
    ("NH-48 Mumbai-Chennai", [(19.08, 72.88), (16.51, 80.65), (13.08, 80.27)]),
    ("NH-16 Kolkata-Chennai", [(22.57, 88.36), (20.30, 85.82), (17.69, 83.22), (13.08, 80.27)]),
    ("NH-27 Guwahati-Siliguri", [(26.14, 91.74), (26.73, 88.42)]),
    ("NH-65 Jodhpur-Surat", [(26.24, 73.02), (23.02, 72.57), (21.17, 72.83)]),
    ("NH-66 Mumbai-Kanyakumari", [(19.08, 72.88), (14.44, 74.86), (11.26, 75.78), (8.52, 76.94)]),
    ("NH-30 Raipur-Jagdalpur", [(21.25, 81.63), (19.07, 82.03)]),
]

RAILWAYS: list[tuple[str, list[tuple[float, float]]]] = [
    ("Delhi-Mumbai Trunk", [(28.61, 77.21), (25.21, 75.86), (22.31, 73.18), (19.08, 72.88)]),
    ("Delhi-Kolkata Trunk", [(28.61, 77.21), (26.85, 80.95), (25.59, 85.14), (23.68, 86.98), (22.57, 88.36)]),
    ("Mumbai-Chennai Trunk", [(19.08, 72.88), (18.52, 73.86), (16.51, 80.65), (13.08, 80.27)]),
    ("Delhi-Chennai Trunk", [(28.61, 77.21), (23.34, 85.31), (17.39, 78.49), (13.08, 80.27)]),
    ("Kolkata-Chennai Trunk", [(22.57, 88.36), (20.30, 85.82), (17.69, 83.22), (13.08, 80.27)]),
    ("Guwahati-New Jalpaiguri", [(26.14, 91.74), (26.73, 88.42)]),
    ("Howrah-Delhi Grand Chord", [(22.57, 88.36), (23.67, 86.15), (24.53, 81.30), (26.22, 78.18), (28.61, 77.21)]),
    ("Konkan Railway", [(19.08, 72.88), (15.85, 74.50), (13.08, 74.79), (11.26, 75.78), (8.52, 76.94)]),
    ("East Coast Railway", [(22.57, 88.36), (21.49, 86.93), (20.30, 85.82), (17.69, 83.22)]),
    ("Howrah-Amritsar", [(22.57, 88.36), (25.59, 85.14), (26.85, 80.95), (28.98, 77.71), (31.63, 74.87)]),
]

# --------------------------------------------------------------------------
# Dataset builder
# --------------------------------------------------------------------------

def build_agriculture_polygons(rng: random.Random) -> list[dict]:
    """Deterministic list of agricultural polygons (lat/lon centers + radius deg).

    Shared by the spatial dataset and the hotspot generator so agriculture-kind
    detections are placed inside real agricultural polygons.
    """
    polys: list[dict] = []
    for state, meta in STATES.items():
        n_poly = 4 if state in ("Punjab", "Haryana", "Uttar Pradesh", "West Bengal") else 3
        for k in range(n_poly):
            a_lat = meta["lat"] + rng.uniform(-1.1, 1.1)
            a_lon = meta["lon"] + rng.uniform(-1.1, 1.1)
            radius = rng.uniform(0.14, 0.3)
            polys.append({
                "name": f"{state} Agricultural Block {k+1}",
                "state": state,
                "lat": a_lat,
                "lon": a_lon,
                "radius_deg": radius,
            })
    return polys


# Agriculture polygons shared between the spatial dataset and hotspot generator
_AGRI_POLYS_CACHE: list[dict] = build_agriculture_polygons(random.Random(SEED))


def build_dataset(rng: Optional[random.Random] = None) -> SpatialDataset:
    rng = rng or random.Random(SEED)
    ds = SpatialDataset()

    # Industrial assets
    for zone in INDUSTRIAL_ZONES:
        code, name, ztype, lat, lon, state, district = zone
        ds.add_point("industrial_area", code, name, lat, lon, {"state": state, "district": district})
    for r in REFINERIES:
        ds.add_point("refinery", r[0], r[1], r[2], r[3], {"state": r[4], "district": r[5]})
    for f in FACTORIES:
        ds.add_point("factory", f[0], f[1], f[2], f[3], {"state": f[4], "district": f[5]})
    for p in POWER_PLANTS:
        ds.add_point("power_plant", p[0], p[1], p[2], p[3], {"state": p[4], "district": p[5]})
    for m in MINES:
        ds.add_point("mine", m[0], m[1], m[2], m[3], {"state": m[4], "district": m[5]})
    # Also add zone anchors to their asset categories so distances resolve
    for zone in INDUSTRIAL_ZONES:
        code, name, ztype, lat, lon, state, district = zone
        asset_type = {
            "Refinery": "refinery",
            "Factory": "factory",
            "Power Plant": "power_plant",
            "Mine": "mine",
        }.get(ztype)
        if asset_type:
            ds.add_point(asset_type, code, name, lat, lon, {"state": state, "district": district, "zone": True})

    # Settlements (sample ~100 deterministically)
    cities = sorted(CITIES, key=lambda c: (c[1], c[0]))
    rng.shuffle(cities)
    for i, (name, state, lat, lon) in enumerate(cities[:100]):
        ds.add_point("settlement", f"ST-{i+1:03d}", name, lat, lon, {"state": state})

    # Forest polygons (radius given in km -> convert to degrees)
    for i, (name, state, lat, lon, radius_km) in enumerate(FORESTS):
        ds.add_geometry(
            "forest", f"FR-{i+1:03d}", name,
            _buffer_circle(lat, lon, radius_km / 111.32), {"state": state},
        )

    # Agriculture polygons: a few per state (shared with the hotspot generator)
    agri_idx = 0
    for poly in build_agriculture_polygons(rng):
        agri_idx += 1
        ds.add_geometry(
            "agriculture",
            f"AG-{agri_idx:03d}",
            poly["name"],
            _buffer_circle(poly["lat"], poly["lon"], poly["radius_deg"]),
            {"state": poly["state"]},
        )

    # Road lines: national corridors + per-state spurs
    road_idx = 0
    for name, waypoints in HIGHWAYS:
        road_idx += 1
        ds.add_geometry("road", f"RD-{road_idx:03d}", name, LineString([(lon, lat) for lat, lon in waypoints]), {})
    for state, meta in STATES.items():
        state_cities = [c for c in cities if c[1] == state]
        if len(state_cities) >= 2:
            for _ in range(3):
                a, b = rng.sample(state_cities, 2)
                road_idx += 1
                ds.add_geometry(
                    "road", f"RD-{road_idx:03d}", f"{state} road link",
                    LineString([(a[3], a[2]), (b[3], b[2])]), {"state": state},
                )

    # Railways
    rw_idx = 0
    for name, waypoints in RAILWAYS:
        rw_idx += 1
        ds.add_geometry("railway", f"RW-{rw_idx:03d}", name, LineString([(lon, lat) for lat, lon in waypoints]), {})

    # Pipelines
    for name, waypoints in PIPELINES:
        rw_idx += 1
        ds.add_geometry("pipeline", f"PL-{rw_idx:03d}", name, LineString([(lon, lat) for lat, lon in waypoints]), {})

    ds.build_indexes()
    return ds


def _buffer_circle(lat: float, lon: float, radius_deg: float) -> Polygon:
    return Point(lon, lat).buffer(radius_deg, quad_segs=12)


# --------------------------------------------------------------------------
# Hotspot generation
# --------------------------------------------------------------------------

def _jitter(lat: float, lon: float, rng: random.Random, km: float) -> tuple[float, float]:
    """Offset a point by up to ``km`` in a random direction."""
    deg = km / 111.32
    angle = rng.uniform(0, 6.28318)
    dx, dy = deg * rng.uniform(0.3, 1.0) * rng.choice([-1, 1]), deg * rng.uniform(0.3, 1.0) * rng.choice([-1, 1])
    return lat + dx, lon + dy * max(0.5, abs(math_cos(lat)))


def math_cos(deg: float) -> float:
    import math

    return math.cos(math.radians(deg))


def _history_for_pattern(
    pattern: str, acquisition: datetime, rng: random.Random, window_days: int = 14
) -> list[datetime]:
    """Generate a deterministic detection history ending at ``acquisition``."""
    if pattern in ("unknown",):
        return []
    if pattern == "sudden":
        # current detection only (history excludes the current one)
        return [acquisition - timedelta(hours=rng.uniform(18, 40))]
    if pattern == "persistent":
        days = sorted(rng.sample(range(1, window_days + 1), rng.randint(8, 12)))
        hours = [rng.uniform(0, 23) for _ in days]
        return [acquisition - timedelta(days=d, hours=h) for d, h in zip(days, hours)]
    if pattern == "recurring":
        clusters = []
        for _ in range(rng.randint(2, 3)):
            base = rng.randint(2, window_days - 1)
            clusters += [base, base - 1]
        return [acquisition - timedelta(days=max(1, d), hours=rng.uniform(0, 20)) for d in sorted(set(clusters))]
    # intermittent
    days = sorted(rng.sample(range(1, window_days + 1), rng.randint(3, 5)))
    return [acquisition - timedelta(days=d, hours=rng.uniform(0, 23)) for d in days]


def generate_hotspot_specs(
    n: int = 320,
    rng: Optional[random.Random] = None,
    now: Optional[datetime] = None,
) -> list[dict]:
    """Generate n hotspot specs (location, thermal params, intended pattern)."""
    rng = rng or random.Random(SEED)
    now = now or datetime.now(timezone.utc)
    specs: list[dict] = []

    for i in range(n):
        kind = rng.random()
        if kind < 0.42:
            zone = rng.choice(INDUSTRIAL_ZONES)
            code, name, ztype, zlat, zlon, state, district = zone
            lat, lon = _jitter(zlat, zlon, rng, km=rng.uniform(0.3, 5.0))
            p = rng.random()
            if p < 0.55:
                pattern = "persistent"
                frp = rng.uniform(15, 110)
                brightness = rng.uniform(325, 400)
            elif p < 0.8:
                pattern = "sudden"
                frp = rng.uniform(40, 160)
                brightness = rng.uniform(350, 425)
            else:
                pattern = "recurring"
                frp = rng.uniform(15, 80)
                brightness = rng.uniform(330, 390)
            # some persistent refinery-adjacent sources are gas flares
            if pattern == "persistent" and ztype in ("Refinery", "Power Plant") and rng.random() < 0.3:
                frp = rng.uniform(80, 180)
                brightness = rng.uniform(365, 420)
            daynight = rng.choice(["D", "D", "D", "N"])
            source_tag = "industrial"
        elif kind < 0.67:
            agri_polys = _AGRI_POLYS_CACHE
            poly = rng.choice(agri_polys)
            state = poly["state"]
            meta = STATES[state]
            lat, lon = _jitter(poly["lat"], poly["lon"], rng, km=rng.uniform(1.0, poly["radius_deg"] * 60.0))
            pattern = rng.choice(["sudden", "sudden", "intermittent", "recurring"])
            frp = rng.uniform(2, 22)
            brightness = rng.uniform(300, 346)
            district = rng.choice(meta["districts"])
            daynight = rng.choice(["D", "D", "D", "D", "N"])
            source_tag = "agriculture"
        elif kind < 0.87:
            fname, state, flat, flon, radius = rng.choice(FORESTS)
            meta = STATES.get(state, {"districts": ["District"]})
            lat, lon = _jitter(flat, flon, rng, km=rng.uniform(0.5, radius * 0.7))
            pattern = rng.choice(["sudden", "sudden", "recurring", "intermittent"])
            frp = rng.uniform(8, 70)
            brightness = rng.uniform(305, 365)
            district = rng.choice(meta["districts"])
            daynight = rng.choice(["D", "D", "N"])
            source_tag = "wildfire"
        else:
            state = rng.choice(list(STATES.keys()))
            meta = STATES[state]
            lat = meta["lat"] + rng.uniform(-2.2, 2.2)
            lon = meta["lon"] + rng.uniform(-2.2, 2.2)
            pattern = rng.choice(["unknown", "sudden", "intermittent"])
            frp = rng.uniform(0.5, 9)
            brightness = rng.uniform(295, 322)
            district = rng.choice(meta["districts"])
            daynight = rng.choice(["D", "N"])
            source_tag = "other"

        acquisition = now - timedelta(hours=rng.uniform(0.5, 24 * 7))
        specs.append(
            {
                "i": i,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "state": state,
                "district": district,
                "brightness": round(brightness, 1),
                "frp": round(frp, 2),
                "confidence": round(rng.uniform(0.6, 1.0), 2),
                "pattern": pattern,
                "daynight": daynight,
                "acquisition": acquisition,
                "source_tag": source_tag,
                "satellite": rng.choice(["VIIRS S-NPP", "VIIRS S-NPP", "VIIRS NOAA-21", "MODIS Aqua", "MODIS Terra"]),
            }
        )
    return specs