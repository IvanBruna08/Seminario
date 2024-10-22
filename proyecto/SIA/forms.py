from django import forms
from .models import Predio, Transporte,Distribuidor, Cliente,Pallet, EnvioPallet, Recepcion, Caja,Pago, EnvioCaja , DistribuidorPallet, TipoCaja
import sys
from django.core.exceptions import ValidationError
from django.utils import timezone
from itertools import cycle
 
def validar_rut(rut):
	rut = rut.upper();
	rut = rut.replace("-","")
	rut = rut.replace(".","")
	aux = rut[:-1]
	dv = rut[-1:]
 
	revertido = map(int, reversed(str(aux)))
	factors = cycle(range(2,8))
	s = sum(d * f for d, f in zip(revertido,factors))
	res = (-s)%11
 
	if str(res) == dv:
		return True
	elif dv=="K" and res==10:
		return True
	else:
		return False

class CustomLoginForm(forms.Form):
    rut = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'RUT'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}))

    def clean(self):
        rut = self.cleaned_data.get('rut')
        password = self.cleaned_data.get('password')

        if not rut or not password:
            raise forms.ValidationError('RUT y contraseña son requeridos.')

        user_found = False
        for model in [Cliente, Predio, Transporte, Distribuidor]:
            try:
                user = model.objects.get(rut=rut)
                if user.password == password:  # Compara directamente
                    self.user = user
                    self.user_type = model.__name__.lower()
                    user_found = True
                    break
            except model.DoesNotExist:
                continue
        
        if not user_found:
            raise forms.ValidationError('Credenciales incorrectas.')

        return self.cleaned_data

class TransporteForm(forms.ModelForm):
    class Meta:
        model = Transporte
        fields = ['nombre', 'auto', 'patente', 'rut', 'billetera']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
        }
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')

        return rut

class PredioForm(forms.ModelForm):
    class Meta:
        model = Predio
        fields = ['nombre', 'direccion','rut','password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
        }
        # Método para validar el RUT
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')

        return rut

class TipoCajaForm(forms.ModelForm):
    class Meta:
        model = TipoCaja
        fields = ['Material', 'capacidad', 'recicable']
        widgets = {
            'Material': forms.TextInput(attrs={'placeholder': 'Ejemplo: Cartón'}),
            'capacidad': forms.NumberInput(attrs={'placeholder': 'Capacidad en kg'}),
            'recicable': forms.CheckboxInput(),
        }

class DistribuidorForm(forms.ModelForm):
    class Meta:
        model = Distribuidor
        fields = ['nombre', 'direccion','rut','password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
        }
        # Método para validar el RUT
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')

        return rut


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'tipo_cliente', 'direccion','rut','password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
        }
        # Método para validar el RUT
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')

        return rut

class PalletForm(forms.ModelForm):
    class Meta:
        model = Pallet
        fields = ['lugar', 'producto', 'clasificacion', 'fecha_cosecha', 'cantidad', 'peso', 'precio_venta']
        widgets = {
            'fecha_cosecha': forms.DateInput(attrs={'type': 'date'}),
            'cantidad': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'Cantidad mínima 70'}),
            'peso': forms.NumberInput(attrs={'step': 'any'}),
            'precio_venta': forms.NumberInput(attrs={'step': 'any'})
        }

    def __init__(self, *args, **kwargs):
        super(PalletForm, self).__init__(*args, **kwargs)
        # Etiquetas personalizadas
        self.fields['lugar'].label = "Huerto"
        self.fields['producto'].label = "Producto"
        self.fields['clasificacion'].label = "Clasificación"
        self.fields['fecha_cosecha'].label = "Fecha de Cosecha"
        self.fields['cantidad'].label = "Cantidad"
        self.fields['peso'].label = "Peso"
        self.fields['precio_venta'].label = "Precio de Venta"

    def clean(self):
        cleaned_data = super().clean()
        peso = cleaned_data.get('peso')
        precio_venta = cleaned_data.get('precio_venta')
        cantidad = cleaned_data.get("cantidad")
        fecha_cosecha = cleaned_data.get("fecha_cosecha")

        if fecha_cosecha and fecha_cosecha > timezone.now().date():
            raise ValidationError("La fecha de cosecha no puede ser una fecha futura.")

        # Validación del peso
        if peso is not None and (peso < 499 or peso > 1200):
            raise ValidationError("El peso debe estar entre 499 y 1200 kg.")

        # Validación del precio de venta
        if precio_venta is not None and (precio_venta < 990 or precio_venta > 5000):
            raise ValidationError("El precio de venta debe estar entre 990 y 5000.")
        
        if cantidad is not None and (cantidad < 70 or cantidad > 240):
            raise ValidationError("Ingrese una cantidad aceptable")
        return cleaned_data


        

class RecepcionForm(forms.ModelForm):
    peso_recepcion = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'step': 'any'}),
        label="Peso Final del Pallet (si hubo variación)"
    )

    class Meta:
        model = Recepcion
        fields = ['estado_recepcion', 'peso_recepcion']  # Incluir el campo de estado y peso final

        widgets = {
            'estado_recepcion': forms.Select()
        }

    def __init__(self, *args, **kwargs):
        super(RecepcionForm, self).__init__(*args, **kwargs)
        self.fields['estado_recepcion'].label = "Estado de Recepción"

class DistribuidorPalletForm(forms.ModelForm):
    class Meta:
        model = DistribuidorPallet
        fields = ['distribuidor', 'peso_enviado']
        widgets = {
            'peso_enviado': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'distribuidor': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, pallet=None, **kwargs):
        super(DistribuidorPalletForm, self).__init__(*args, **kwargs)
        self.pallet = pallet  # Guardar el empaque

        self.fields['distribuidor'].label = "Seleccionar Distribuidor"
        self.fields['peso_enviado'].label = "Peso de la Caja (kg)"
        self.fields['distribuidor'].queryset = Distribuidor.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        peso_enviado = cleaned_data.get("peso_enviado")

        if self.pallet and peso_enviado:
            # Usar un valor por defecto de 0 si el peso_caja es None
            peso_existente = sum(distribuidorpallet.peso_enviado or 0 for distribuidorpallet in DistribuidorPallet.objects.filter(pallet=self.pallet))
            if (peso_existente + peso_enviado) > self.pallet.peso_pallet:
                self.add_error('peso_enviado', "El peso total para distribución excede el peso del pallet.")
        return cleaned_data

class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['tipo_caja']
        widgets = {
            'tipo_caja': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, recepcion=None, **kwargs):
        super(CajaForm, self).__init__(*args, **kwargs)
        self.recepcion = recepcion  # Guardar la recepción si es necesario

        # Ajustar la etiqueta del campo tipo_caja si es necesario
        self.fields['tipo_caja'].label = "Tipo de Caja"
        
        # Definir el queryset de tipo_caja
        self.fields['tipo_caja'].queryset = TipoCaja.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        tipo_caja = cleaned_data.get('tipo_caja')












