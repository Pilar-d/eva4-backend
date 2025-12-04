# accounts/utils.py

import re

def validar_rut(rut):
    """
    Implementa el algoritmo de validación del RUT chileno (con o sin guión/puntos).
    """
    # 1. Limpiar y estandarizar
    rut = rut.upper().replace('.', '').replace('-', '')
    
    if not rut:
        return False

    # 2. Separar RUT y Dígito Verificador (DV)
    dv_ingresado = rut[-1]
    rut_sin_dv = rut[:-1]
    
    if not rut_sin_dv.isdigit():
        return False
    
    # 3. Cálculo del Dígito Verificador (DV)
    i = 2
    suma = 0
    
    for d in reversed(rut_sin_dv):
        suma += int(d) * i
        i += 1
        if i == 8:
            i = 2
            
    resto = suma % 11
    dv_calculado = 11 - resto

    if dv_calculado == 10:
        dv_calculado = 'K'
    elif dv_calculado == 11:
        dv_calculado = '0'
    else:
        dv_calculado = str(dv_calculado)

    # 4. Comparación
    return dv_calculado == dv_ingresado

# Nota: Esta función es utilizada en serializers como ProductSerializer o SupplierSerializer
# [cite_start]para cumplir con el requisito de validar datos sensibles locales (RUT chileno). [cite: 29, 87, 186]