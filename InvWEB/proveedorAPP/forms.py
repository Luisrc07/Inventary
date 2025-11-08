# -------------------------------------------------------------------------
# Copyright (C) 2025 Luisrc07 - Luis Rodriguez
#
# Este programa es software libre: usted puede redistribuirlo y/o modificarlo
# bajo los términos de la Licencia Pública General GNU publicada
# por la Free Software Foundation, ya sea la versión 3 de la Licencia,
# o (a su elección) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil, pero
# SIN NINGUNA GARANTÍA; sin incluso la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR.
# Consulte la Licencia Pública General GNU para más detalles.
#
# Usted debería haber recibido una copia de la Licencia Pública General GNU
# junto con este programa. Si no, consulte <https://www.gnu.org/licenses/>.
# -------------------------------------------------------------------------

from django import forms 
from proveedorAPP.models import Proveedor
from django.forms import TextInput, Textarea, Select, NumberInput, EmailInput

tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'



class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre','rif','telefono','email','direccion', 'activo']
        widgets= {
            'nombre': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'rif': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'telefono': TextInput(attrs={'class': tailwind_class, 'required': 'True'}),
            'email': EmailInput(attrs={'class': tailwind_class}),
            'direccion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
        }
