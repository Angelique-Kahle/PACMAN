import emcee
import os
import numpy as np
import pickle
from scipy.stats import norm
from uncertainties import ufloat
from . import plots
from . import util


def get_step_size(params, meta, fit_par):
    nvisit = int(meta.nvisit)
    step_size = []

    ii = 0
    for i in range(int(len(params)/nvisit)):
            if fit_par['fixed'][ii].lower() == "false":
                    if str(fit_par['tied'][ii]) == "-1":
                        step_size.append(fit_par['step_size'][ii])
                        ii = ii + 1
                    else:
                        for j in range(nvisit):
                            step_size.append(fit_par['step_size'][ii])
                            ii = ii + 1
            else:
                ii = ii + 1

    return np.array(step_size)


def mcmc_fit(data, model, params, file_name, meta, fit_par):
    theta = util.format_params_for_sampling(params, meta, fit_par)
    ndim, nwalkers = len(theta), meta.run_nwalkers

    print('Run emcee...')
    sampler = emcee.EnsembleSampler(nwalkers, ndim, lnprob, args = (params, data, model, meta, fit_par))
    step_size = get_step_size(params, meta, fit_par)
    pos = [theta + np.array(step_size)*np.random.randn(ndim) for i in range(nwalkers)]
    sampler.run_mcmc(pos, meta.run_nsteps, progress=True)

    if not os.path.isdir(meta.workdir + meta.fitdir + '/mcmc_res'):
        os.makedirs(meta.workdir + meta.fitdir + '/mcmc_res')

    pickle.dump([data, params, sampler.chain], open(meta.workdir + meta.fitdir + '/mcmc_res/' +  '/mcmc_out_bin{0}_wvl{1:0.3f}.p'.format(meta.s30_file_counter, meta.wavelength), "wb"))
    nburn = meta.run_nburn

    if meta.run_nsteps * meta.run_nwalkers > 1000000:
        thin_corner = int((meta.run_nsteps - meta.run_nburn) * meta.run_nwalkers // 100000)
        print('Note: Big Corner plot with many steps. Thinning Plot by factor: {0}'.format(thin_corner))
    else:
        thin_corner = 1

    labels = meta.labels

    samples = sampler.chain[:, nburn::thin_corner, :].reshape((-1, ndim))
    plots.mcmc_pairs(samples, params, meta, fit_par, data)
    plots.mcmc_chains(ndim, sampler, 0, labels, meta)
    plots.mcmc_chains(ndim, sampler, nburn, labels, meta)

    medians = []
    errors_lower = []
    errors_upper = []
    for i in range(len(theta)):
        q = util.quantile(samples[:, i], [0.16, 0.5, 0.84])
        medians.append(q[1])
        errors_lower.append(abs(q[1] - q[0]))
        errors_upper.append(abs(q[2] - q[1]))

    f_mcmc = open(meta.workdir + meta.fitdir + '/mcmc_res/' + "/mcmc_res_bin{0}_wvl{1:0.3f}.txt".format(meta.s30_file_counter, meta.wavelength), 'w')
    for row in zip(errors_lower, medians, errors_upper, labels):
        print('{0: >8}: '.format(row[3]), '{0: >24} '.format(row[1]), '{0: >24} '.format(row[0]), '{0: >24} '.format(row[2]), file=f_mcmc)
    f_mcmc.close()

    updated_params = util.format_params_for_Model(medians, params, meta, fit_par)
    fit = model.fit(data, updated_params)
    plots.plot_fit_lc2(data, fit, meta, mcmc=True)
    meta.rms_list_emcee.append(fit.rms)

    return medians, errors_lower, errors_upper


def lnprior(theta, data):
    lnprior_prob = 0.
    n = len(data.prior)
    for i in range(n):
        if data.prior[i][0] == 'U': 
            if np.logical_or(theta[i] < data.prior[i][1], 
              theta[i] > data.prior[i][2]): lnprior_prob += - np.inf
        if data.prior[i][0] == 'N': 
            lnprior_prob -= 0.5*(np.sum(((theta[i] - 
              data.prior[i][1])/data.prior[i][2])**2 + 
              np.log(2.0*np.pi*(data.prior[i][2])**2)))
    return lnprior_prob
    


def lnprob(theta, params, data, model, meta, fit_par):
    updated_params = util.format_params_for_Model(theta, params, meta, fit_par)
    fit = model.fit(data, updated_params)
    lp = lnprior(theta, data)
    return fit.ln_like + lp


#ORDER
#mcmc_fit
#format_params_for_mcmc
#mcmc_fit
#lnprob
#format_params_for_Model
#lnprob
#lnprior
#lnprob



