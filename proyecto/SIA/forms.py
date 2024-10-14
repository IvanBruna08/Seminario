from django import forms
from .models import Predio, Transporte,Distribuidor, Cliente,Pallet, EnvioPallet, Recepcion, Caja,Pago, EnvioCaja , DistribuidorPallet
import sys
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
        fields = ['nombre', 'auto', 'patente', 'rut','password', 'billetera']
        # Método para validar el RUT
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')

        return rut

class PredioForm(forms.ModelForm):
    class Meta:
        model = Predio
        fields = ['nombre', 'direccion', 'billetera','rut','password']
        # Método para validar el RUT
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')

        return rut

class DistribuidorForm(forms.ModelForm):
    class Meta:
        model = Distribuidor
        fields = ['nombre', 'direccion', 'billetera','rut','password']
        # Método para validar el RUT
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')

        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')

        return rut


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'tipo_cliente', 'direccion', 'billetera','rut','password']
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
            'cantidad': forms.NumberInput(attrs={'step': 'any'}),
            'peso': forms.NumberInput(attrs={'step': 'any'}),
            'precio_venta': forms.NumberInput(attrs={'step': 'any'})
        }

    def __init__(self, *args, **kwargs):
        super(PalletForm, self).__init__(*args, **kwargs)
        # Etiquetas personalizadas
        self.fields['lugar'].label = "Lugar"
        self.fields['producto'].label = "Producto"
        self.fields['clasificacion'].label = "Clasificación"
        self.fields['fecha_cosecha'].label = "Fecha de Cosecha"
        self.fields['cantidad'].label = "Cantidad"
        self.fields['peso'].label = "Peso"
        self.fields['precio_venta'].label = "Precio de Venta"
        

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
            peso_existente = sum(distribuidorpallet.peso_enviado or 0 for distribuidorpallet in DistirbuidorPallet.objects.filter(pallet=self.pallet))
            if (peso_existente + peso_enviado) > self.pallet.peso_pallet:
                self.add_error('peso_enviado', "El peso total para distribución excede el peso del pallet.")
        return cleaned_data

class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['cliente', 'peso_caja', 'tipo_caja']
        widgets = {
            'peso_caja': forms.NumberInput(attrs={'step': 'any', 'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'tipo_caja': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, recepcion=None, **kwargs):
        super(CajaForm, self).__init__(*args, **kwargs)
        self.recepcion = recepcion  # Guardar el empaque

        self.fields['cliente'].label = "Seleccionar Cliente"
        self.fields['peso_caja'].label = "Peso de la Caja (kg)"
        self.fields['tipo_caja'].label = "Tipo de Caja"
        self.fields['cliente'].queryset = Cliente.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        peso_caja = cleaned_data.get("peso_caja")

        # Validar que el peso_caja no sea menor a 0
        if peso_caja is not None and peso_caja < 0:
            self.add_error('peso_caja', "El peso de la caja no puede ser menor a 0.")

        if self.recepcion and peso_caja:
            # Usar un valor por defecto de 0 si el peso_caja es None
            peso_existente = sum(caja.peso_caja or 0 for caja in Caja.objects.filter(recepcion=self.recepcion))
            if (peso_existente + peso_caja) > self.recepcion.peso_recepcion:
                self.add_error('peso_caja', "El peso total de las cajas excede el peso del pallet.")
        return cleaned_data













