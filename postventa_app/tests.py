from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from django.contrib.auth.models import User

from .models import (
	Constructora,
	Proyecto,
	Categoria,
	Propietario,
	Tecnico,
	Reclamo,
	Cita,
)


class CitasFlowTests(TestCase):
	def setUp(self):
		# Usuarios
		self.user_prop = User.objects.create_user(username='prop1', password='test1234', email='prop1@example.com')
		self.user_tec = User.objects.create_user(username='tec1', password='test1234', email='tec1@example.com')

		# Constructora y dependencias
		self.constructora = Constructora.objects.create(
			rut='76.123.456-7',
			razon_social='Constructora XYZ S.A.',
			nombre_comercial='XYZ',
			email_principal='contacto@xyz.com',
			telefono='+56 2 234567',
			direccion='Av. Siempre Viva 123',
			plan='basico',
			fecha_inicio_contrato=date.today(),
			estado='activo',
		)

		self.proyecto = Proyecto.objects.create(
			constructora=self.constructora,
			codigo='PRJ-001',
			nombre='Proyecto Alfa',
			ubicacion='Santiago',
			cantidad_unidades=10,
			estado='entregado',
		)

		self.categoria = Categoria.objects.create(nombre='Electricidad')

		# Propietario
		self.propietario = Propietario.objects.create(
			user=self.user_prop,
			nombre='Juan Pérez',
			rut='12.345.678-9',
			email='prop1@example.com',
			telefono='+56 9 1234 5678',
			direccion='Depto 101',
			proyecto=self.proyecto,
		)

		# Técnico
		self.tecnico = Tecnico.objects.create(
			constructora=self.constructora,
			usuario=self.user_tec,
			especialidad='Electricidad',
			telefono='+56 9 2222 3333',
			estado='disponible',
		)

		# Reclamo base
		self.reclamo = Reclamo.objects.create(
			propietario=self.propietario,
			proyecto=self.proyecto,
			categoria=self.categoria,
			ubicacion_especifica='Torre A, 101',
			descripcion='Falla eléctrica en dormitorio',
			estado='pendiente',
		)
		# Asignar técnico después para que save() actualice fecha_asignacion/estado si corresponde
		self.reclamo.tecnico_asignado = self.tecnico
		self.reclamo.save()

		# Cita confirmada inicial para pruebas
		mañana = date.today() + timedelta(days=1)
		self.cita = Cita.objects.create(
			reclamo=self.reclamo,
			tecnico=self.tecnico,
			propietario=self.propietario,
			fecha_cita=mañana,
			hora_inicio=time(9, 0),
			hora_fin=time(11, 0),
			estado='confirmada',
			fecha_confirmacion=timezone.now(),
		)

		# Autenticar
		self.client.force_login(self.user_prop)

	def test_cancelar_cita_cancels_and_updates_reclamo_state(self):
		url = reverse('cancelar_cita', args=[self.cita.id])
		resp = self.client.post(url, data={'motivo': 'No puedo en ese horario'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp.status_code, 200)
		# Refrescar instancias
		self.cita.refresh_from_db()
		self.reclamo.refresh_from_db()

		self.assertEqual(self.cita.estado, 'cancelada')
		self.assertIsNotNone(self.cita.fecha_cancelacion)
		self.assertIn('No puedo', self.cita.motivo_cancelacion or '')
		# Como el reclamo mantiene técnico asignado y no hay otras citas activas, debe quedar en 'asignado'
		self.assertEqual(self.reclamo.estado, 'asignado')

	def test_reagendar_cita_updates_same_row_and_reclamo_fields(self):
		# Crear una segunda cita para este escenario, activa
		pasado_mañana = date.today() + timedelta(days=2)
		cita2 = Cita.objects.create(
			reclamo=self.reclamo,
			tecnico=self.tecnico,
			propietario=self.propietario,
			fecha_cita=pasado_mañana,
			hora_inicio=time(10, 0),
			hora_fin=time(12, 0),
			estado='pendiente',
		)

		url = reverse('reagendar_cita', args=[cita2.id])
		nuevo_dia = date.today() + timedelta(days=3)
		slot = f"{nuevo_dia.isoformat()}|14:00|16:00"
		resp = self.client.post(url, data={'slot': slot})
		# Debe redirigir a mis_reclamos
		self.assertEqual(resp.status_code, 302)

		old_id = cita2.id
		cita2.refresh_from_db()
		self.reclamo.refresh_from_db()

		# Misma fila (no se crea nueva)
		self.assertEqual(cita2.id, old_id)
		self.assertEqual(cita2.fecha_cita, nuevo_dia)
		self.assertEqual(cita2.hora_inicio, time(14, 0))
		self.assertEqual(cita2.hora_fin, time(16, 0))
		self.assertEqual(cita2.estado, 'confirmada')
		self.assertIsNotNone(cita2.fecha_confirmacion)
		# Reclamo debe estar al menos en 'asignado' y con fecha_asignacion poblada
		self.assertEqual(self.reclamo.estado, 'asignado')
		self.assertIsNotNone(self.reclamo.fecha_asignacion)
		# fecha_primera_visita debe existir (si no estaba) o mantenerse
		self.assertIsNotNone(self.reclamo.fecha_primera_visita)

	def test_cancelar_reclamo_sets_estado_and_cancels_active_citas(self):
		# Crear una cita activa adicional
		pasado_mañana = date.today() + timedelta(days=2)
		cita_activa = Cita.objects.create(
			reclamo=self.reclamo,
			tecnico=self.tecnico,
			propietario=self.propietario,
			fecha_cita=pasado_mañana,
			hora_inicio=time(13, 0),
			hora_fin=time(15, 0),
			estado='confirmada',
			fecha_confirmacion=timezone.now(),
		)

		url = reverse('cancelar_reclamo', args=[self.reclamo.id])
		resp = self.client.post(url, data={'motivo': 'No deseo continuar'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(resp.status_code, 200)

		# Refrescar
		self.reclamo.refresh_from_db()
		self.cita.refresh_from_db()
		cita_activa.refresh_from_db()

		self.assertEqual(self.reclamo.estado, 'cancelado')
		self.assertEqual(self.cita.estado, 'cancelada')
		self.assertEqual(cita_activa.estado, 'cancelada')

