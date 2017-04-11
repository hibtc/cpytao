# encoding: utf-8
"""
Utility functions for use with pytao.
"""

from __future__ import absolute_import
from __future__ import unicode_literals

from math import sqrt

#----------------------------------------
# Time transformations
#----------------------------------------

# From Bmad manual, p236f, sec 13.2.2
# Bmad: PZ = ΔP / P₀    =
# MADX: PT = ΔE / P₀c
# PTC:  PT = ΔE / P₀    =
# Bmad:  Z = β c Δt     = β  T(MADX)
# MADX:  T =   c Δt
# PTC:   T =     Δt     = T(MADX) / c

# P = β γ m c   = β E / c
# E =   γ m c²
#       β =          P c     /     E

def t_to_z(t, pt, M, E0):
    """Transform canonical coordinates: t,pt -> z,pz (i.e. MAD-X to Bmad)."""
    P0    = sqrt(E0**2 - M**2)
    E1    = E0 + P0 * pt
    P1    = sqrt(E1**2 - M**2)
    bet_0 = P0 / E0
    bet_1 = P1 / E1
    z    = bet_1 * t
    pz   = (P1 - P0)/P0
    return z, pz


def z_to_t(z, pz, beta, e_tot, p0c, **ignore):
    """Transform canonical coordinates: z,pz -> t,pt (i.e. Bmad to MAD-X)."""
    t  =   z   /beta
    pt = (pz+1)/beta - e_tot/p0c
    return t, pt
