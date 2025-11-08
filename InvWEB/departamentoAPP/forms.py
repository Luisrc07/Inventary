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
from departamentoAPP.models import Departamento
from django.forms import TextInput, Textarea, Select, NumberInput, EmailInput
from django.core.validators import RegexValidator


tailwind_class = 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'

solo_numeros_validator = RegexValidator(
    regex=r'^\d+$', # Expresión regular que solo permite dígitos
    message="Este campo debe contener solo dígitos numéricos (0-9)."
)




class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nombre','descripcion','activo']
        widgets= { 
        'nombre':TextInput(attrs={'class':tailwind_class}),
        'descripcion': Textarea(attrs={'class': tailwind_class, 'rows':2}),
        }
