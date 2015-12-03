#!/usr/bin/env python

import re
import sys
import requests


CABS_ENDPOINT = 'http://biocomp.chem.uw.edu.pl/CABSdock'


def get_csrf_token(html_content):
    """Get cross site request forgery token an html content.

    :param html_content: String containing the page content.

    :return: String containing the csrf token.
    """
    return re.search(
        '<input .* name="csrf_token" .* value="(.+)">',
        html_content
    ).groups()[0]


def submit_job(pdb_receptor, pdb_file, ligand_sequence, simulation_cycles=5):
    """Submit a job to the CASB-dock server.

    :param pdb_receptor: PDB code (and chain) for the receptor.
    :param pdb_file: Path to the PDB file.
    :param ligand_sequence: Aminoacid sequence for the ligand.
    :param simulation_cycles: Number of cycles for the simulation.

    :return: URL to query the submitted job.
    """
    # Get cookie from home page
    response = requests.get(CABS_ENDPOINT)
    response.raise_for_status()
    cookies = response.cookies

    params = {
        # Mandatory parameters
        'pdb_receptor': pdb_receptor,
        'ligand_seq': ligand_sequence,
        'length': simulation_cycles,

        # Optional parameters
        'ligand_ss': '',
        'name': 'Test docking project',
        'email': '',
        'show': 'y',  # 'y' to not show job on the queue

        'csrf_token': get_csrf_token(response.text),
    }

    files = {'receptor_file': open(pdb_file, 'rb')}
    response = requests.post(
        CABS_ENDPOINT, data=params, files=files,
        cookies=cookies, allow_redirects=False
    )
    response.raise_for_status()
    if 'redirected automatically to target URL' not in response.text:
        raise Exception('Job submission to the CABS server was rejected.')
    return re.search('href="(.+)"', response.text).groups()[0]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Syntax:\n /cabs-dock.py ligand pdb_codes_file'
    else:
        with open(sys.argv[2]) as pdb_codes_file:
            pdb_codes = pdb_codes_file.read().splitlines()
            ligand = sys.argv[1]
            if len(ligand) < 4:
                raise ValueError('Ligand must contain at least 4 residues.')

            for pdb_receptor in pdb_codes:
                pdb_file = pdb_receptor.split(':')[0] + '.pdb'
                job_url = submit_job(pdb_receptor, pdb_file, ligand)
                print 'http://biocomp.chem.uw.edu.pl' + job_url
