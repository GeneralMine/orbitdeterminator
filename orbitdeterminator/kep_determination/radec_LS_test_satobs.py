# TODO: evaluate Earth ephemeris only once for a given TDB instant
# this implies saving all UTC times and their TDB equivalencies

from least_squares import xyz_frame_, meanmotion
import gauss_method as gm
import numpy as np
from astropy.time import Time
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

# path of file of optical IOD-formatted observations
# the example contains tracking data for satellite USA 74
body_fname_str = '../example_data/SATOBS-ML-19200716.txt' # body_fname_str = '../example_data/iss_radec_generated_horizons.txt'

#body name
body_name_str = 'ISS (25544)'

#lines of observations file to be used for orbit determination
obs_arr = [2, 3, 4, 5] # ML observations of ISS on 2016 Jul 19 and 20 # obs_arr = [7, 10, 13] # simulated observations generated from HORIZONS for ISS on 2018 Aug 08

# load IOD data for a given satellite
iod_object_data = gm.load_iod_data(body_fname_str)
# print('IOD observation data:\n', iod_object_data[ np.array(obs_arr)-1 ], '\n')

#load data of listed observatories (longitude, latitude, elevation)
sat_observatories_data = gm.load_sat_observatories_data('sat_tracking_observatories.txt')
# print('sat_observatories_data = ', sat_observatories_data)

#the total number of observations used
nobs = len(obs_arr)

#select adequate index of Gauss polynomial root
r2_root_ind_vec = np.zeros((nobs-2,), dtype=int)
# r2_root_ind_vec[4] = 1 # modify as necessary if adequate root of Gauss polynomial has to be selected

#get preliminary orbit using Gauss method
#q0 : a, e, taup, I, W, w, T
q0 = np.array(gm.gauss_method_sat(body_fname_str, body_name_str, obs_arr, r2_root_ind_vec, refiters=10, plot=False))
x0 = q0[0:6]
x0[3:6] = np.deg2rad(x0[3:6])

obs_arr_ls = np.array(range(1, 6+1)) # obs_arr_ls = np.array(range(1, 31+1))
print('obs_arr_ls = ', obs_arr_ls)
# print('obs_arr_ls[0] = ', obs_arr_ls[0])
# print('obs_arr_ls[-1] = ', obs_arr_ls[-1])
nobs_ls = len(obs_arr_ls)
# print('nobs_ls = ', nobs_ls)

rov = gm.radec_obs_vec(obs_arr_ls, iod_object_data)
print('rov = ', rov)
print('len(rov) = ', len(rov))

rv0 = gm.radec_res_vec_rov(x0, obs_arr_ls, iod_object_data, sat_observatories_data, rov)
Q0 = np.linalg.norm(rv0, ord=2)/len(rv0)

print('rv0 = ', rv0)
print('Q0 = ', Q0)

Q_ls = least_squares(gm.radec_res_vec_rov, x0, args=(obs_arr_ls, iod_object_data, sat_observatories_data, rov), method='lm', xtol=1e-13)

print('INFO: scipy.optimize.least_squares exited with code', Q_ls.status)
print(Q_ls.message,'\n')
print('Q_ls.x = ', Q_ls.x)

tv_star, rv_star = gm.t_radec_res_vec(Q_ls.x, obs_arr_ls, iod_object_data, sat_observatories_data, rov)
Q_star = np.linalg.norm(rv_star, ord=2)/len(rv_star)
print('rv* = ', rv_star)
print('Q* = ', Q_star)

print('Total residual evaluated at Gauss solution: ', Q0)
print('Total residual evaluated at least-squares solution: ', Q_star, '\n')
# # print('Percentage improvement: ', (Q0-Q_star)/Q0*100, ' %')

print('Observational arc:')
print('Number of observations: ', len(obs_arr_ls))
print('First observation (UTC) : ', Time(tv_star[0], format='jd').iso)
print('Last observation (UTC) : ', Time(tv_star[-1], format='jd').iso)

n_num = meanmotion(gm.mu_Earth, Q_ls.x[0])

print('\nOrbital elements, Gauss + least-squares solution:')
# print('Reference epoch (t0):                ', t_mean)
print('Semi-major axis (a):                 ', Q_ls.x[0], 'km')
print('Eccentricity (e):                    ', Q_ls.x[1])
print('Time of pericenter passage (tau):    ', Time(Q_ls.x[2], format='jd').iso, 'JDUTC')
print('Pericenter altitude (q):             ', Q_ls.x[0]*(1.0-Q_ls.x[1])-gm.Re, 'km')
print('Apocenter altitude (Q):              ', Q_ls.x[0]*(1.0+Q_ls.x[1])-gm.Re, 'km')
# print('True anomaly at epoch (f0):          ', np.rad2deg(time2truean(Q_ls.x[0], Q_ls.x[1], gm.mu_Sun, t_mean, Q_ls.x[2])), 'deg')
print('Argument of pericenter (omega):      ', np.rad2deg(Q_ls.x[3]), 'deg')
print('Inclination (I):                     ', np.rad2deg(Q_ls.x[4]), 'deg')
print('Longitude of Ascending Node (Omega): ', np.rad2deg(Q_ls.x[5]), 'deg')
print('Orbital period (T):                  ', 2.0*np.pi/n_num/60.0, 'min')

ra_res_vec = np.rad2deg(rv_star[0::2])*(3600.0)
dec_res_vec = np.rad2deg(rv_star[1::2])*(3600.0)

# print('len(ra_res_vec) = ', len(ra_res_vec))
# print('len(dec_res_vec) = ', len(dec_res_vec))
# print('nobs_ls = ', nobs_ls)
# print('len(tv_star) = ', len(tv_star))
# # print('tv_star = ', tv_star)

# y_rad = 0.001

f, axarr = plt.subplots(2, sharex=True)
axarr[0].set_title('Gauss + LS fit residuals: RA, Dec')
axarr[0].scatter(tv_star, ra_res_vec, s=0.75, label='delta RA (\")')
axarr[0].set_ylabel('RA (\")')
axarr[1].scatter(tv_star, dec_res_vec, s=0.75, label='delta Dec (\")')
axarr[1].set_xlabel('time (JDUTC)')
axarr[1].set_ylabel('Dec (\")')
# # plt.xlim(4,5)
# # plt.ylim(-y_rad, y_rad)
plt.show()

npoints = 1000
theta_vec = np.linspace(0.0, 2.0*np.pi, npoints)
x_orb_vec = np.zeros((npoints,))
y_orb_vec = np.zeros((npoints,))
z_orb_vec = np.zeros((npoints,))

for i in range(0,npoints):
    x_orb_vec[i], y_orb_vec[i], z_orb_vec[i] = xyz_frame_(Q_ls.x[0], Q_ls.x[1], theta_vec[i], Q_ls.x[3], Q_ls.x[4], Q_ls.x[5])

ax = plt.axes(aspect='equal', projection='3d')

# Earth-centered orbits: Computed orbit and Earth's
ax.scatter3D(0.0, 0.0, 0.0, color='blue', label='Earth')
# ax.scatter3D(x_vec, y_vec, z_vec, color='red', marker='+')
ax.plot3D(x_orb_vec, y_orb_vec, z_orb_vec, 'red', linewidth=0.5, label=body_name_str+' orbit')
plt.legend()
ax.set_xlabel('x (km)')
ax.set_ylabel('y (km)')
ax.set_zlabel('z (km)')
xy_plot_abs_max = np.max((np.amax(np.abs(ax.get_xlim())), np.amax(np.abs(ax.get_ylim()))))
ax.set_xlim(-xy_plot_abs_max, xy_plot_abs_max)
ax.set_ylim(-xy_plot_abs_max, xy_plot_abs_max)
ax.set_zlim(-xy_plot_abs_max, xy_plot_abs_max)
ax.legend(loc='center left', bbox_to_anchor=(1.04,0.5)) #, ncol=3)
ax.set_title('Satellite orbit (Gauss+LS): '+body_name_str)
plt.show()

# print(' = ', )

