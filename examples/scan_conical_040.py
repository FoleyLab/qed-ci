import numpy as np
import csv
import os
import shutil
from ase import Atoms
from ase.io import write
from ase.calculators.calculator import Calculator, all_changes
from ase.optimize import BFGS
from ase.io.trajectory import Trajectory

import sys
#sys.path.append("/home/nvu12/software/qed_ci_main/qed_ci_casscf9/qed-ci/src/")
#sys.path.append("/home/nvu12/software/qed_ci_main/qed_ci_112123/qed-ci/src/")

import psi4
from helper_PFCI import PFHamiltonianGenerator
from helper_PFCI import Determinant
from helper_cqed_rhf import cqed_rhf
from nuclear_grad import *
np.set_printoptions(threshold=sys.maxsize)

# (Use your existing options_dict and cavity_options from lih_surface5.py)
options_dict = {
    'basis': 'cc-pvdz',
    'scf_type': 'pk',
    'soscf': 'true',
    # 3. Add Level Shifting
    # This pushes virtual orbitals higher in energy during the SCF cycle,
    # preventing them from mixing incorrectly with the occupied orbitals.
    'level_shift': 0.1,
    'e_convergence': 1e-8,
    'd_convergence': 1e-8,
    'restricted_docc': [6],
    'active': [7],
    'num_roots':1
}

cavity_options = {
    'omega_value' : 0.1212727168509417,
    'lambda_vector' : np.array([0.4, 0.0, 0.00]),
    'ignore_coupling' : False,
    'number_of_photons' : 1,
    'ci_level' : 'cas',
    'davidson_roots' : 2,
    'nact_orbs' : 7,
    'nact_els' : 4,
    'coherent_state_basis' : True,
    'spin_adaptation': "singlet",
    'davidson_threshold' : 1e-7,
    'davidson_maxdim': 21,
    'davidson_maxiter':100,
    'davidson_indim':11,
}

# --- 1. INITIAL GEOMETRY (Ethylene) ---
# Atoms: 0-H, 1-H, 2-H, 3-H, 4-C, 5-C
# Note: H0 has a seeded 0.05 Z-displacement to initiate pyramidalization
initial_pos = [
       ( 0.94368426,       0.83299107,       0.17952050),
       (-1.25498268,       0.12262672,      -0.83372399),
       ( 1.21934695,      -0.86659013,       0.13530237),
       (-0.97000204,       0.05432156,       0.94371435),
       ( 0.67473940,      -0.12061313,      -0.33561803),
       (-0.61278588,      -0.02273609,      -0.03919522)
]
syms = ['H', 'H', 'H', 'H', 'C', 'C']
mol = Atoms(syms, positions=initial_pos)

def find_mecp(atoms, state_p, state_q, max_steps=500, step_size=0.1,
              prefix='mecp_040', restart_from_step=None):
    """
    MECP search with:
    - Orbital restart between steps
    - Adaptive step size
    - Geometry saved at every step (XYZ + trajectory)
    - CSV logging of branching vectors
    - Ability to restart from a saved geometry
    - Automatic backup of orbital and occupation files
    """
    
    print(f"{'='*60}")
    print(f"MECP search: states {state_p} and {state_q}")
    print(f"Cavity: lambda={cavity_options['lambda_vector']}, omega={cavity_options['omega_value']:.6f}")
    print(f"Step size: {step_size}, Max steps: {max_steps}")
    print(f"{'='*60}")
    
    # --- File setup ---
    csv_file = f'{prefix}_vectors.csv'
    traj_file = f'{prefix}_trajectory.traj'
    geom_dir = f'{prefix}_geometries'
    data_dir = f'{prefix}_casscf_data' # Added directory for output files
    
    os.makedirs(geom_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True) 
    
    # Restart logic
    start_step = 0
    if restart_from_step is not None:
        restart_xyz = f'{geom_dir}/step_{restart_from_step:04d}.xyz'
        if os.path.exists(restart_xyz):
            atoms = read(restart_xyz)
            start_step = restart_from_step
            print(f"Restarting from step {restart_from_step}: {restart_xyz}")
        else:
            print(f"WARNING: {restart_xyz} not found, starting from initial geometry")
    
    # CSV header (only write if starting fresh)
    if start_step == 0:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['step', 'R_CC', 'gap_eV', 'f_seam_norm', 'cos_phi', 'e_p', 'e_q']
            for i, s in enumerate(atoms.get_chemical_symbols()):
                header.extend([f'gx_{s}{i}', f'gy_{s}{i}', f'gz_{s}{i}'])
            for i, s in enumerate(atoms.get_chemical_symbols()):
                header.extend([f'hx_{s}{i}', f'hy_{s}{i}', f'hz_{s}{i}'])
            writer.writerow(header)
    
    # Trajectory writer
    traj = Trajectory(traj_file, 'a')  # append mode for restarts
    
    # Enable orbital restart
    cavity_options['save_orbital'] = True
    
    for step in range(start_step, start_step + max_steps):
        
        # --- Orbital restart: use previous orbitals after first step ---
        if step >= start_step:
            cavity_options['use_orbital_guess'] = True
        #else:
        #    cavity_options['use_orbital_guess'] = False
        #    # Clean orbital file on fresh start
        #    if start_step == 0 and os.path.exists('orbital.out'):
        #        os.remove('orbital.out')
        
        # --- Build geometry string ---
        pos = atoms.get_positions()
        symbols = atoms.get_chemical_symbols()
        mol_str = "\n".join([f"{s} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" 
                             for s, p in zip(symbols, pos)])
        mol_str += "\nunits angstrom\nsymmetry c1\nno_reorient\nnocom"
        
        # --- Compute gradients and coupling (reuse job object) ---
        job = nuclear_grad(mol_str, options_dict, cavity_options)
        
        job.compute_grad(state_p, state_p)
        grad_p = np.array(job.total_gradient).reshape(-1, 3)
        e_p = job.eigenvals[state_p]
        #if not job.casscf_converged:
        #    print(f"Step {step}: SA-CASSCF failed on state {state_p} gradient. Rolling back.")
        #    if step > start_step:
        #        atoms = read(f'{geom_dir}/step_{step-1:04d}.xyz')
        #    step_size *= 0.5
        #    cavity_options['use_orbital_guess'] = False
        #    print(f"  New step size: {step_size}")
        #    continue    
        job.compute_grad(state_q, state_q)
        grad_q = np.array(job.total_gradient).reshape(-1, 3)
        e_q = job.eigenvals[state_q]
        
        job.compute_grad(state_p, state_q)
        h = np.array(job.h0).reshape(-1, 3)
         
        # --- MECP math ---
        gap = (e_q - e_p) * 27.2114  # eV
        g = grad_q - grad_p
        sigma = 0.5 * (grad_p + grad_q)
        
        u_g = g / np.linalg.norm(g)
        cos_phi = np.abs(np.dot(u_g.flatten(), h.flatten()) / np.linalg.norm(h))
        
        # Symmetry breaking kick
        if cos_phi > 0.98:
            print(f"Step {step}: Symmetry detected (cos_phi={cos_phi:.3f}). Applying kick...")
            kick = np.zeros_like(pos)
            kick[0, 2] = 0.05
            atoms.set_positions(pos + kick)
            continue
        
        # Gram-Schmidt orthogonalization
        h_perp = h - np.dot(h.flatten(), u_g.flatten()) * u_g
        u_h = h_perp / np.linalg.norm(h_perp)
        
        # Forces
        f_gap = gap * u_g
        f_seam = sigma - np.dot(sigma.flatten(), u_g.flatten()) * u_g \
                       - np.dot(sigma.flatten(), u_h.flatten()) * u_h
        
        total_force = -(f_gap + f_seam)
        f_seam_norm = np.linalg.norm(f_seam)
        
        # --- Adaptive step size ---
        if abs(gap) < 0.01:
            effective_step = min(step_size, 0.05)  # Smaller near seam
        else:
            effective_step = step_size
        
        # --- Save geometry BEFORE updating ---
        curr_r = atoms.get_distance(4, 5)
        
        # Save as XYZ with metadata in comment line
        step_xyz = f'{geom_dir}/step_{step:04d}.xyz'
        comment = f"Step={step} Gap={gap:.8f}eV R_CC={curr_r:.5f}A f_seam={f_seam_norm:.6e} cos_phi={cos_phi:.4f}"
        write(step_xyz, atoms, comment=comment)
        
        # Save to trajectory
        atoms.info['step'] = step
        atoms.info['gap_eV'] = gap
        atoms.info['f_seam_norm'] = f_seam_norm
        traj.write(atoms)

        # --- Backup CASSCF Output Files ---
        # Copies the files generated by this successful step to the data directory
        for f_name in ['orbital.out', 'occupation_number.out', 'natural_orbital.out']:
            if os.path.exists(f_name):
                base, ext = os.path.splitext(f_name)
                # Create a filename like 'orbital_step_0035.out' in the data_dir
                dest = os.path.join(data_dir, f"{base}_step_{step:04d}{ext}")
                shutil.copy(f_name, dest)
        
        # --- Log to CSV ---
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([step, curr_r, gap, f_seam_norm, cos_phi, 
                           e_p, e_q, *g.flatten(), *h.flatten()])
        
        # --- Print status ---
        print(f"Step {step:4d}: Gap={gap:12.8f} eV | R_CC={curr_r:.5f} A | "
              f"cos(phi)={cos_phi:.3f} | f_seam={f_seam_norm:.4e} | step={effective_step:.3f}")
        
        # --- Convergence check ---
        if abs(gap) < 1e-4 and f_seam_norm < 5e-4:
            print(f"\n{'='*60}")
            print(f"MECP CONVERGED at step {step}!")
            print(f"  R_CC = {curr_r:.5f} A")
            print(f"  Gap  = {gap:.8f} eV")
            print(f"  f_seam norm = {f_seam_norm:.6e}")
            print(f"  cos(phi) = {cos_phi:.4f}")
            print(f"{'='*60}")
            write(f'{prefix}_converged.xyz', atoms, comment=comment)
            break
        
        # --- Update positions ---
        atoms.set_positions(pos + effective_step * total_force)
    
    traj.close()
    
    # Save final geometry regardless of convergence
    write(f'{prefix}_final.xyz', atoms)
    print(f"\nFinal geometry saved to {prefix}_final.xyz")
    print(f"All step geometries in {geom_dir}/")
    print(f"CASSCF output logs saved in {data_dir}/")
    print(f"Branching vectors in {csv_file}")
    
    return atoms
 
# ==========================================
# 5. RUN
# ==========================================
 
# Fresh start:
mecp_geometry = find_mecp(mol, state_p=0, state_q=1, max_steps=500, 
                          step_size=0.1, prefix='mecp_040')
 
# To restart from step 35 (if SA-CASSCF failed there):
# mecp_geometry = find_mecp(mol, state_p=0, state_q=1, max_steps=500,
#                           step_size=0.05, prefix='mecp_030', restart_from_step=35)
