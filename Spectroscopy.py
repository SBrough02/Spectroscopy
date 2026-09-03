#Synthetic model
import numpy as np
import matplotlib.pyplot as plt
from scipy.constants import h, c, k

def planck_equation(wavelength, temperature):
    return 2*h*c/wavelength**5 * 1/(np.exp((h*c)/(wavelength*temperature*k))-1)

wavelength_nanometers = np.linspace(200, 2000, 200)
wavelength_meters = wavelength_nanometers*10**-9
flux = planck_equation(wavelength_meters, 5000)

h2o_bands = [
    (720, 40, 0.2),
    (940, 50, 0.3),
    (1130, 50, 0.25),
    (1400, 80, 0.5),
    (1900, 100, 0.6),
    (2600, 120, 0.4),
    (3100, 150, 0.3),
]

centers, widths, depths = zip(*h2o_bands)
centers = np.array(centers) * 10**(-9)
widths = np.array(widths)
depths = np.array(depths)

fwhm = 100*10**(-9)
sigma = fwhm / 2.355

def insert_dips(wavelength, flux, centers, widths, depths):
    flux_with_dips = flux.copy()
    for center, width, depth in zip(centers, widths, depths):
        dip = 1 - depth * np.exp(-((wavelength_meters - center)**2) / (2 * sigma**2))
        flux_with_dips *= dip
    return flux_with_dips

flux_with_dips = insert_dips(wavelength_meters, flux, centers, widths, depths)
signal_noise_ratio = 25
noise_std = (flux_with_dips) / signal_noise_ratio
noise = np.random.normal(0, noise_std)
flux_with_dips_and_noise = flux_with_dips + noise

error = np.abs(flux_with_dips_and_noise - flux_with_dips)

plt.plot(wavelength_meters, flux)
plt.ylabel('Flux(W/m^-2/m^-1)')
plt.xlabel('Wavelength(m)')
plt.title('Figure 1 - Flux vs wavelength')
plt.show()

plt.plot(wavelength_meters, flux_with_dips)
plt.ylabel('Flux(W/m^-2/m^-1)')
plt.xlabel('Wavelength(m)')
plt.title('Figure 2 - Flux vs wavelength showing dips due to H20 molecules')
plt.show()

plt.errorbar(wavelength_meters, flux_with_dips_and_noise, yerr=error, markersize=2, elinewidth=1, capsize=4, fmt='o', zorder=1)
plt.plot(wavelength_meters,flux_with_dips, zorder=2)
plt.ylabel('Flux(W/m^-2/m^-1)')
plt.xlabel('Wavelength(m)')
plt.title('Figure 3 - Flux vs wavelength after light passes a stationary\n atmosphere showing dips due to H20 molecules')
plt.show()

#Platon model

import numpy as np
import matplotlib.pyplot as plt

star_data = np.loadtxt('Stardata.txt')
wavelength = star_data[:, 0]
wavelength_unc = star_data[:, 1]
radius_ratio = np.sqrt(star_data[:, 2]) 
radius_ratio_unc = star_data[:, 3] / 2 * np.sqrt(star_data[:, 2])

plt.errorbar(wavelength, radius_ratio, yerr=radius_ratio_unc, xerr = wavelength_unc, markersize=2, elinewidth=1, capsize=4, fmt='o', zorder=1)
plt.ylabel('Rp/Rs')
plt.xlabel('Wavelength(micro m)')
plt.title('Figure 5 - Rp/Rs vs wavelength for HD189733B')
plt.show()

import platon
from platon.constants import R_sun, M_jup, R_jup, M_sun, AU
from platon.transit_depth_calculator import TransitDepthCalculator


planet_radius = 1.138 * R_jup
planet_mass = 1.138 * M_jup 
stellar_radius = 0.805 * R_sun 
temperature = 1200
semi_major_axis = 0.031 * AU

calculator = TransitDepthCalculator()

wavelengths, depths, _ = calculator.compute_depths(
    star_radius=stellar_radius,
    planet_mass=planet_mass,
    planet_radius=planet_radius,
    temperature=temperature, 
)

print(depths)

depths = np.sqrt(depths)
wavelengths = wavelengths / 1e-6 
bin_edges = np.arange(wavelengths.min(), wavelengths.max(), 0.1)
bin_indices = np.digitize(wavelengths, bins=bin_edges)
binned_wavelengths = [wavelengths[bin_indices == i].mean() for i in range(1, len(bin_edges))]
binned_depths = [depths[bin_indices == i].mean() for i in range(1,len(bin_edges))]


plt.plot(binned_wavelengths, binned_depths)
plt.xlim(0,5)
plt.ylabel('Modelled Rp/Rs')
plt.xlabel('Wavelength(micro m)')
plt.title('Figure 6 - Modelled Rp/Rs vs wavelength produced by Platon for HD189733B')
plt.show()

#Chi squared analysis
import numpy as np
from scipy.optimize import minimize
from scipy.interpolate import interp1d
import platon
from platon.constants import R_sun, M_jup, R_jup
from platon.transit_depth_calculator import TransitDepthCalculator
import matplotlib.pyplot as plt
from platon._hydrostatic_solver import AtmosphereError
from scipy.optimize import differential_evolution

!pip install numdifftools
import numdifftools as nd

star_data = np.loadtxt('Stardata.txt')
wavelength = star_data[:, 0] * 1e-6
radius_ratio = np.sqrt(star_data[:, 2])
radius_ratio_unc = star_data[:, 3] / (2 * np.sqrt(star_data[:, 2]))

calculator_2 = TransitDepthCalculator()

planet_radius = 1.138 * R_jup 
planet_mass = 1.138 * M_jup 
stellar_radius = 0.805 * R_sun 

last_model = None

def chi_squared(params):
    global last_model
    logZ, CO_ratio, log10_cloudtop, offset = params
    cloudtop_pressure = 10**log10_cloudtop

    
    planet_radius = 1.138 * R_jup 
    planet_mass = 1.138 * M_jup 
    
    
    star_radius = 0.805 * R_sun 
    star_temperature = 4875
    
    try:
        wavelengths_model, depths_model, _, = calculator_2.compute_depths(
        star_radius,
        planet_mass,
        planet_radius,
        temperature = 1200,
        logZ = logZ,
        CO_ratio = CO_ratio,
        cloudtop_pressure = cloudtop_pressure
        )
    except AtmosphereError:
        return 1e12 

    depths_interp = np.interp(wavelength, wavelengths_model, depths_model)
    
    radius_ratio_model = np.sqrt(depths_interp) + offset

    last_model = radius_ratio_model
    

    chi2 = np.sum(((radius_ratio - radius_ratio_model) ** 2) / radius_ratio_unc**2)
    return chi2

initial_guess = [ 1.0, 0.7, 2.0, 0.01]
bounds = [
    (0.0, 1.5),
    (0.1, 1.0),
    (0.0, 4.0),
    (-0.02, 0.02)
]



init_logZ, init_CO, init_cloud, init_offset = initial_guess
init_cloudtop_pressure = 10**init_cloud


wavelengths_model, depths_model, _ = calculator_2.compute_depths(
    stellar_radius,
    planet_mass,
    planet_radius,
    temperature=1200,
    logZ=init_logZ,
    CO_ratio=init_CO,
    cloudtop_pressure=init_cloudtop_pressure
)


radius_ratio_model = np.sqrt(np.interp(wavelength, wavelengths_model, depths_model)) + init_offset


result_global = differential_evolution(chi_squared, bounds, polish=True)

best_logZ_g, best_CO_ratio_g, best_log10_cloudtop_g, best_offset_g = result_global.x
best_cloudtop_pressure_g = 10**best_log10_cloudtop_g

print("Global optimizer results (Differential Evolution)")
print('Best_logZ:', best_logZ_g)
print('Best CO ratio:', best_CO_ratio_g)
print('Best log10 cloudtop:', best_log10_cloudtop_g, "-> P =", best_cloudtop_pressure_g, "Pa ", 'or', best_cloudtop_pressure_g/10**5, 'bar')
print('Best offset:', best_offset_g)
print("Minimum chi-squared:", result_global.fun)
print("Reduced chi-squared:", result_global.fun / len(wavelength))

plt.plot(wavelength, radius_ratio)
plt.ylabel('Rp/Rs')
plt.xlabel('Wavelength(micro m)')
plt.title('Figure 5 - Rp/Rs vs wavelength for HD189733B')
plt.show()


wavelengths_model, depths_model, _ = calculator_2.compute_depths(
    stellar_radius,
    planet_mass,
    planet_radius,
    temperature=1200,
    logZ=best_logZ_g,
    CO_ratio=best_CO_ratio_g,
    cloudtop_pressure=best_cloudtop_pressure_g
)

depths_model_offset = np.sqrt(depths_model) + best_offset_g
wavelengths_model = wavelengths_model / 1e-6 
bin_edges_2 = np.arange(wavelengths_model.min(), wavelengths_model.max(), 0.1)
bin_indices_2 = np.digitize(wavelengths_model, bins=bin_edges_2)
binned_wavelengths_2 = [wavelengths_model[bin_indices_2 == i].mean() for i in range(1, len(bin_edges_2))]
binned_depths_2 = [depths_model_offset[bin_indices_2 == i].mean() for i in range(1,len(bin_edges_2))]

plt.plot(binned_wavelengths_2, binned_depths_2)
plt.xlim(0,5)
plt.ylabel('Modelled Rp/Rs')
plt.xlabel('Wavelength(micro m)')
plt.title('χ²-minimised PLATON fit to the transmission spectrum of HD 189733b')
plt.show()



# Get Hessian (matrix of 2nd derivatives) at best-fit point
hessian_fun = nd.Hessian(chi_squared, step=0.01)
hessian = hessian_fun(result_global.x)

# Invert Hessian to get covariance matrix
cov_matrix = np.linalg.pinv(hessian)

# 1-sigma uncertainties
uncertainties = np.sqrt(np.diag(cov_matrix))
print("Uncertainties:", uncertainties)
