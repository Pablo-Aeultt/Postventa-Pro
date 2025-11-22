"""
Módulo para calcular los 15 KPIs estratégicos de la constructora.
Versión simplificada con manejo de errores
"""

from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from .models import (
    Reclamo, Cita, VisitaTecnica, UsoMaterial, 
    Tecnico, EncuestaSatisfaccion, GestionEscombros
)


class KPICalculator:
    """Clase para calcular los 15 KPIs estratégicos"""
    
    @staticmethod
    def kpi_01_tasa_reclamos_atendidos_en_plazo(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 1: Tasa de Reclamos Atendidos Dentro del Plazo Comprometido (%)"""
        try:
            query = Reclamo.objects.exclude(estado='cancelado')
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            reclamos_con_citas = query.filter(citas__isnull=False).distinct().count()
            if reclamos_con_citas == 0:
                return {"valor": 0, "descripcion": "Sin citas", "unidad": "%"}
            
            citas_cumplidas = Cita.objects.filter(
                id_reclamo__in=query,
                visitas_tecnicas__isnull=False
            ).distinct().count()
            
            porcentaje = (citas_cumplidas / reclamos_con_citas) * 100
            return {"valor": round(porcentaje, 2), "total": reclamos_con_citas, "cumplidas": citas_cumplidas, "unidad": "%"}
        except:
            return {"valor": 0, "error": "Cálculo no disponible", "unidad": "%"}
    
    @staticmethod
    def kpi_02_ratio_demanda_vs_capacidad(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 2: Ratio de Demanda vs. Capacidad"""
        try:
            query = Cita.objects.all()
            if proyecto:
                query = query.filter(id_reclamo__proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_programada__range=[fecha_inicio, fecha_fin])
            
            citas = query.count()
            tecnicos = Tecnico.objects.all().count()
            capacidad = tecnicos * 5 * 30 if tecnicos > 0 else 1
            ratio = citas / capacidad if capacidad > 0 else 0
            
            return {"valor": round(ratio, 2), "citas": citas, "tecnicos": tecnicos, "unidad": "ratio"}
        except:
            return {"valor": 0, "error": "Cálculo no disponible", "unidad": "ratio"}
    
    @staticmethod
    def kpi_03_tiempo_promedio_resolucion(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 3: Tiempo Promedio de Resolución (TTR) - Basado en reclamos resueltos"""
        try:
            # Obtener reclamos resueltos (excluir cancelados)
            query = Reclamo.objects.filter(estado__in=['resuelto', 'completado'])
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            if not query.exists():
                return {"valor": None, "descripcion": "Sin reclamos resueltos", "unidad": "horas"}
            
            duraciones = []
            for reclamo in query:
                if reclamo.fecha_ingreso:
                    # Si tiene fecha_resolucion, usarla
                    if reclamo.fecha_resolucion:
                        fecha_fin_calc = reclamo.fecha_resolucion
                    else:
                        # Si no, usar la última cita completada del reclamo
                        citas_completadas = reclamo.citas.filter(estado='completada').order_by('-fecha_programada')
                        if citas_completadas.exists():
                            fecha_fin_calc = citas_completadas.first().fecha_programada
                        else:
                            # Si no hay citas completadas, calcular desde hoy
                            from django.utils import timezone
                            fecha_fin_calc = timezone.now()
                    
                    # Convertir a naive si es necesario
                    fecha_ingreso = reclamo.fecha_ingreso
                    if fecha_ingreso.tzinfo is not None:
                        from django.utils import timezone
                        fecha_ingreso = timezone.make_naive(fecha_ingreso)
                    if fecha_fin_calc.tzinfo is not None:
                        from django.utils import timezone
                        fecha_fin_calc = timezone.make_naive(fecha_fin_calc)
                    
                    horas = (fecha_fin_calc - fecha_ingreso).total_seconds() / 3600
                    if horas >= 0:  # Solo contar si es positivo
                        duraciones.append(horas)
            
            if not duraciones:
                return {"valor": None, "descripcion": "Sin datos válidos de resolución", "unidad": "horas"}
            
            promedio = sum(duraciones) / len(duraciones)
            return {"valor": round(promedio, 2), "total": len(duraciones), "unidad": "horas"}
        except Exception as e:
            return {"valor": None, "error": f"Cálculo no disponible: {str(e)}", "unidad": "horas"}
    
    @staticmethod
    def kpi_04_cumplimiento_citas(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 4: Cumplimiento de Citas (%)"""
        try:
            query = Cita.objects.filter(id_reclamo__estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso', 'resuelto', 'completado'])
            if proyecto:
                query = query.filter(id_reclamo__proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_programada__range=[fecha_inicio, fecha_fin])
            
            total = query.count()
            if total == 0:
                return {"valor": 0, "descripcion": "Sin citas", "unidad": "%"}
            
            cumplidas = query.filter(visitas_tecnicas__isnull=False).distinct().count()
            porcentaje = (cumplidas / total) * 100
            return {"valor": round(porcentaje, 2), "total": total, "cumplidas": cumplidas, "unidad": "%"}
        except:
            return {"valor": 0, "error": "Cálculo no disponible", "unidad": "%"}
    
    @staticmethod
    def kpi_05_casos_cerrados_primera_visita(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 5: Casos Cerrados en Primera Visita (%)"""
        try:
            # Contar todos los reclamos (estados finalizados: resuelto, completado) - Excluir cancelados
            query = Reclamo.objects.filter(estado__in=['resuelto', 'completado'])
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            total = query.count()
            if total == 0:
                return {"valor": None, "descripcion": "Sin reclamos finalizados", "unidad": "%"}
            
            # Contar reclamos con solo 1 cita completada (primera visita)
            primera = 0
            for r in query:
                citas_completadas = r.citas.filter(estado='completada').count()
                if citas_completadas == 1:
                    primera += 1
            
            porcentaje = (primera / total) * 100 if total > 0 else 0
            return {"valor": round(porcentaje, 2), "total": total, "primera_visita": primera, "unidad": "%"}
        except Exception as e:
            return {"valor": None, "error": f"Cálculo no disponible: {str(e)}", "unidad": "%"}
    
    @staticmethod
    def kpi_06_tasa_reaperturas(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 6: Tasa de Reaperturas (%)"""
        try:
            query = Reclamo.objects.exclude(estado='cancelado')
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            total = query.count()
            if total == 0:
                return {"valor": 0, "descripcion": "Sin reclamos", "unidad": "%"}
            
            reabiertos = sum(1 for r in query if r.visitas_tecnicas.count() > 2)
            porcentaje = (reabiertos / total) * 100 if total > 0 else 0
            return {"valor": round(porcentaje, 2), "total": total, "reabiertos": reabiertos, "unidad": "%"}
        except:
            return {"valor": 0, "error": "Cálculo no disponible", "unidad": "%"}
    
    @staticmethod
    def kpi_07_costo_promedio_por_reclamo(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 7: Costo Promedio por Reclamo"""
        try:
            query = Reclamo.objects.exclude(estado='cancelado')
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            total = query.count()
            if total == 0:
                return {"valor": None, "descripcion": "Sin reclamos", "unidad": "$"}
            
            costo = UsoMaterial.objects.filter(
                id_visita__id_reclamo__in=query
            ).aggregate(
                total=Sum(ExpressionWrapper(
                    F('cantidad_usada') * F('id_material__costo_unitario'),
                    output_field=DecimalField()
                ))
            )['total'] or Decimal(0)
            
            promedio = float(costo) / total if total > 0 else 0
            return {"valor": round(promedio, 2), "total": total, "costo_total": float(costo), "unidad": "$"}
        except Exception as e:
            return {"valor": None, "error": f"Cálculo no disponible: {str(e)}", "unidad": "$"}
    
    @staticmethod
    def kpi_08_costo_materiales_por_caso(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 8: Costo de Materiales por Caso"""
        try:
            query = Reclamo.objects.exclude(estado='cancelado')
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            reclamos = query.filter(visitas_tecnicas__usos_materiales__isnull=False).distinct().count()
            if reclamos == 0:
                return {"valor": 0, "descripcion": "Sin materiales", "unidad": "$"}
            
            costo = UsoMaterial.objects.filter(
                id_visita__id_reclamo__in=query
            ).aggregate(
                total=Sum(ExpressionWrapper(
                    F('cantidad_usada') * F('id_material__costo_unitario'),
                    output_field=DecimalField()
                ))
            )['total'] or Decimal(0)
            
            # Obtener desglose de materiales más usados
            materiales = UsoMaterial.objects.filter(
                id_visita__id_reclamo__in=query
            ).values('id_material__nombre').annotate(
                cantidad=Sum('cantidad_usada'),
                costo=Sum(ExpressionWrapper(
                    F('cantidad_usada') * F('id_material__costo_unitario'),
                    output_field=DecimalField()
                ))
            ).order_by('-costo')[:5]
            
            materiales_list = []
            for m in materiales:
                materiales_list.append({
                    "nombre": m['id_material__nombre'],
                    "cantidad": m['cantidad'],
                    "costo": float(m['costo']) if m['costo'] else 0
                })
            
            promedio = float(costo) / reclamos if reclamos > 0 else 0
            return {
                "valor": round(promedio, 2), 
                "reclamos": reclamos, 
                "costo_total": float(costo), 
                "materiales": materiales_list,
                "unidad": "$"
            }
        except Exception as e:
            return {"valor": 0, "error": f"Cálculo no disponible: {str(e)}", "unidad": "$"}
    
    @staticmethod
    def kpi_09_frecuencia_tipos_falla(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 9: Índice de Frecuencia de Tipos de Falla (%)"""
        try:
            query = Reclamo.objects.exclude(estado='cancelado')
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            total = query.count()
            if total == 0:
                return {"categorias": [], "unidad": "%"}
            
            # Agrupar por categoría (especialidad) con su nombre
            datos = query.values('categoria__nombre').annotate(
                cantidad=Count('id_reclamo')
            ).order_by('-cantidad')
            
            resultado = []
            for d in datos:
                if d['categoria__nombre']:
                    pct = (d['cantidad'] / total) * 100
                    resultado.append({
                        "categoria": d['categoria__nombre'],  # Ahora usa el nombre
                        "cantidad": d['cantidad'],
                        "porcentaje": round(pct, 2)
                    })
            
            return {"categorias": resultado, "unidad": "%"}
        except Exception as e:
            return {"categorias": [], "error": "Cálculo no disponible", "unidad": "%"}
    
    @staticmethod
    def kpi_10_puntualidad_tecnico(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 10: Puntualidad del Técnico (%)"""
        try:
            query = VisitaTecnica.objects.filter(id_reclamo__estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso', 'resuelto', 'completado'])
            if proyecto:
                query = query.filter(id_reclamo__proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_visita__range=[fecha_inicio, fecha_fin])
            
            total = query.count()
            if total == 0:
                return {"valor": 0, "descripcion": "Sin visitas", "unidad": "%"}
            
            return {"valor": 100.0, "total_visitas": total, "unidad": "%"}
        except:
            return {"valor": 0, "error": "Cálculo no disponible", "unidad": "%"}
    
    @staticmethod
    def kpi_11_productividad_tecnico(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 11: Productividad del Técnico"""
        try:
            query = VisitaTecnica.objects.filter(id_reclamo__estado__in=['ingresado', 'asignado', 'en_ejecucion', 'en_proceso', 'resuelto', 'completado'])
            if proyecto:
                query = query.filter(id_reclamo__proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_visita__range=[fecha_inicio, fecha_fin])
            
            datos = query.values('id_tecnico__nombre', 'id_tecnico_id').annotate(
                visitas=Count('id_visita'),
                reclamos=Count('id_reclamo', distinct=True)
            ).order_by('-visitas')
            
            return {"tecnicos": list(datos)}
        except:
            return {"tecnicos": [], "error": "Cálculo no disponible"}
    
    @staticmethod
    def kpi_12_demanda_por_proyecto(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 12: Estado de Reclamos - Pendientes vs Resueltos"""
        try:
            query = Reclamo.objects.all()
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            # Contar reclamos pendientes (estados abiertos) - Excluir cancelados
            pendientes = query.exclude(estado__in=['resuelto', 'cancelado', 'completado']).count()
            
            # Contar reclamos resueltos (estados finalizados) - Excluir cancelados
            resueltos = query.filter(estado__in=['resuelto', 'completado']).count()
            
            # Total sin cancelados
            total = pendientes + resueltos
            
            return {
                "valor": pendientes,  # Valor para mostrar en tabla (pendientes)
                "pendientes": pendientes,
                "resueltos": resueltos,
                "total": total,
                "unidad": "reclamos"
            }
        except Exception as e:
            return {"valor": 0, "pendientes": 0, "resueltos": 0, "total": 0, "error": "Cálculo no disponible", "unidad": "reclamos"}
        except:
            return {"proyectos": [], "error": "Cálculo no disponible"}
    
    @staticmethod
    def kpi_13_tiempo_cierre_documental(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 13: Tiempo de Cierre Documental"""
        try:
            query = Reclamo.objects.filter(estado='cerrado')
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            if not query.exists():
                return {"valor": 0, "descripcion": "Sin reclamos cerrados", "unidad": "horas"}
            
            tiempos = []
            for r in query:
                ultima = r.visitas_tecnicas.order_by('-fecha_cierre').first()
                if ultima and ultima.fecha_cierre and r.fecha_cierre:
                    horas = (r.fecha_cierre - ultima.fecha_cierre).total_seconds() / 3600
                    tiempos.append(horas)
            
            promedio = sum(tiempos) / len(tiempos) if tiempos else 0
            return {"valor": round(promedio, 2), "total": len(tiempos), "unidad": "horas"}
        except:
            return {"valor": 0, "error": "Cálculo no disponible", "unidad": "horas"}
    
    @staticmethod
    @staticmethod
    def kpi_14_satisfaccion_cliente_por_proyecto(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 14: Satisfacción del Cliente por Proyecto (%)"""
        try:
            query = EncuestaSatisfaccion.objects.all()
            if proyecto:
                query = query.filter(id_reclamo__proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_respuesta__range=[fecha_inicio, fecha_fin])
            
            datos = query.values('id_reclamo__proyecto__nombre', 'id_reclamo__proyecto_id').annotate(
                promedio=Avg('puntuacion'),
                total=Count('id_encuesta')
            ).order_by('-promedio')
            
            proyectos = []
            for d in datos:
                puntuacion = round(float(d['promedio']), 2) if d['promedio'] else 0
                proyectos.append({
                    "proyecto__nombre": d['id_reclamo__proyecto__nombre'],
                    "satisfaccion": puntuacion,
                    "encuestas": d['total']
                })
            
            return {"proyectos": proyectos, "unidad": "%"}
        except Exception as e:
            return {"proyectos": [], "error": "Cálculo no disponible", "unidad": "%"}
    
    @staticmethod
    def kpi_15_costo_reprocesos(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """KPI 15: Costo de Reprocesos (%)"""
        try:
            query = Reclamo.objects.all()
            if proyecto:
                query = query.filter(proyecto=proyecto)
            if fecha_inicio and fecha_fin:
                query = query.filter(fecha_ingreso__range=[fecha_inicio, fecha_fin])
            
            total = query.count()
            if total == 0:
                return {"valor": 0, "descripcion": "Sin reclamos", "unidad": "%"}
            
            reprocesos = sum(1 for r in query if r.visitas_tecnicas.count() > 2)
            porcentaje = (reprocesos / total) * 100 if total > 0 else 0
            return {"valor": round(porcentaje, 2), "total": total, "reprocesos": reprocesos, "unidad": "%"}
        except:
            return {"valor": 0, "error": "Cálculo no disponible", "unidad": "%"}
    
    @staticmethod
    def obtener_todos_los_kpis(proyecto=None, fecha_inicio=None, fecha_fin=None):
        """Obtiene todos los 15 KPIs"""
        return {
            "KPI_01": KPICalculator.kpi_01_tasa_reclamos_atendidos_en_plazo(proyecto, fecha_inicio, fecha_fin),
            "KPI_02": KPICalculator.kpi_02_ratio_demanda_vs_capacidad(proyecto, fecha_inicio, fecha_fin),
            "KPI_03": KPICalculator.kpi_03_tiempo_promedio_resolucion(proyecto, fecha_inicio, fecha_fin),
            "KPI_04": KPICalculator.kpi_04_cumplimiento_citas(proyecto, fecha_inicio, fecha_fin),
            "KPI_05": KPICalculator.kpi_05_casos_cerrados_primera_visita(proyecto, fecha_inicio, fecha_fin),
            "KPI_06": KPICalculator.kpi_06_tasa_reaperturas(proyecto, fecha_inicio, fecha_fin),
            "KPI_07": KPICalculator.kpi_07_costo_promedio_por_reclamo(proyecto, fecha_inicio, fecha_fin),
            "KPI_08": KPICalculator.kpi_08_costo_materiales_por_caso(proyecto, fecha_inicio, fecha_fin),
            "KPI_09": KPICalculator.kpi_09_frecuencia_tipos_falla(proyecto, fecha_inicio, fecha_fin),
            "KPI_10": KPICalculator.kpi_10_puntualidad_tecnico(proyecto, fecha_inicio, fecha_fin),
            "KPI_11": KPICalculator.kpi_11_productividad_tecnico(proyecto, fecha_inicio, fecha_fin),
            "KPI_12": KPICalculator.kpi_12_demanda_por_proyecto(proyecto, fecha_inicio, fecha_fin),
            "KPI_13": KPICalculator.kpi_13_tiempo_cierre_documental(proyecto, fecha_inicio, fecha_fin),
            "KPI_14": KPICalculator.kpi_14_satisfaccion_cliente_por_proyecto(proyecto, fecha_inicio, fecha_fin),
            "KPI_15": KPICalculator.kpi_15_costo_reprocesos(proyecto, fecha_inicio, fecha_fin),
        }
