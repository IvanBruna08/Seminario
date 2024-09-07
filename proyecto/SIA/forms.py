from django import forms

class CosechaForm(forms.Form):
    producto = forms.CharField(label='Producto', max_length=100)
    fecha_cosecha = forms.DateField(label='Fecha de Cosecha', widget=forms.DateInput(attrs={'type': 'date'}))
    ubicacion = forms.CharField(label='Ubicación', max_length=255)
    cantidad_lote = forms.IntegerField(label='Cantidad del Lote(Kg)')
    cantidad_agua = forms.IntegerField(label='Cantidad de Agua (litros)')
    pesticidas_fertilizantes = forms.CharField(label='Pesticidas y Fertilizantes', widget=forms.Textarea)
    practicas_cultivo = forms.CharField(label='Prácticas de Cultivo', widget=forms.Textarea)

class MarcarTransportadoForm(forms.Form):
    id_cosecha = forms.IntegerField(label='ID de la cosecha')

class RegistroTransporteForm(forms.Form):
    fecha = forms.DateField(label='Fecha')
    destino = forms.CharField(label='Destino')
    transportista = forms.CharField(label='Transportista')
    id_cosecha = forms.IntegerField(label='ID de la Cosecha', required=True)  # Campo para el ID de la 

class ActualizarEstadoTransporteForm(forms.Form):
    id = forms.IntegerField(label='ID del Transporte')
    status = forms.ChoiceField(
        choices=[
            (0, 'En Camino'),
            (1, 'Entregado'),
            (2, 'Retrasado')
        ],
        label='Estado'
    ) 

class PlacaForm(forms.Form):
    placa = forms.CharField(max_length=100, label='Placa del Auto')