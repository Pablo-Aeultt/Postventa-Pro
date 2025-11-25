from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import Propietario, Tecnico, Perfil


class PropietarioBackend(BaseBackend):
    """
    Backend de autenticación que permite login con RUT o Email del Propietario.
    Crea usuarios User de Django automáticamente si no existen.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica usando RUT o Email del cliente
        username: puede ser RUT (con o sin formato) o email
        password: contraseña del usuario o RUT limpio del cliente
        """
        if not username or not password:
            return None

        # Limpiar RUT (quitar puntos y guiones)
        username_limpio = username.replace('.', '').replace('-', '').upper()
        password_limpio = password.replace('.', '').replace('-', '').upper()

        try:
            cliente = None

            # 1) Intentar buscar por RUT exacto
            try:
                cliente = Propietario.objects.get(rut__iexact=username)
            except Propietario.DoesNotExist:
                cliente = None

            # 2) Si no, buscar comparando RUT limpio
            if not cliente:
                for c in Propietario.objects.all():
                    c_rut_limpio = (c.rut or '').replace('.', '').replace('-', '').upper()
                    if c_rut_limpio and c_rut_limpio == username_limpio:
                        cliente = c
                        break

            # 3) Si aún no, buscar por email en Propietario
            if not cliente:
                try:
                    cliente = Propietario.objects.get(email__iexact=username)
                except Propietario.DoesNotExist:
                    cliente = None
            
            # 4) Si aún no hay cliente, buscar por email en User y luego obtener propietario
            if not cliente:
                try:
                    user = User.objects.get(email__iexact=username)
                    cliente = Propietario.objects.get(user=user)
                except (User.DoesNotExist, Propietario.DoesNotExist):
                    return None

            if not cliente:
                return None

            # Normalizar rut del cliente
            rut_limpio = (cliente.rut or '').replace('.', '').replace('-', '').upper()

            # Intentar encontrar un User existente (por username=rut_limpio o por email)
            user = None
            try:
                user = User.objects.get(username__iexact=rut_limpio)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email__iexact=(cliente.email or ''))
                except User.DoesNotExist:
                    user = None

            # Si existe User y la contraseña coincide, autenticar con ese User
            if user and user.check_password(password):
                return user

            # Permitir autenticación usando el RUT limpio como contraseña
            # Si coincide, creamos/actualizamos un User asociado
            if password_limpio == rut_limpio:
                # Si no existe user, crear uno con username=rut_limpio
                username_to_use = rut_limpio
                if user is None:
                    # Asegurar unicidad de username
                    if User.objects.filter(username=username_to_use).exists():
                        if username_limpio:
                            username_to_use = f"{username_to_use}_{cliente.id}"
                    user = User.objects.create_user(
                        username=username_to_use,
                        email=(cliente.email or ''),
                        password=password,
                    )
                else:
                    # Si existe user pero la contraseña no coincidía, actualizarla
                    user.set_password(password)
                    user.save()

                return user

            # Si no coincide ninguna regla, no autenticar
            return None

        except Exception:
            return None
    
    def get_user(self, user_id):
        """Obtiene un usuario por ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class TecnicoBackend(BaseBackend):
    """
    Backend de autenticación para Técnicos.
    Permite iniciar sesión con RUT del técnico (con o sin formato) o email del usuario vinculado.
    Reglas:
      - Si encuentra el técnico por RUT o por email (de su usuario), usa ese User.
      - Si la contraseña coincide, autentica.
      - Opcionalmente permite usar RUT limpio como contraseña para facilitar primeros accesos (igual que propietarios).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        u_in = (username or '').strip()
        p_in = (password or '').strip()

        # Limpieza de RUT de entrada
        u_clean = u_in.replace('.', '').replace('-', '').upper()

        try:
            tecnico = None
            user = None
            
            # 1) Buscar por RUT exacto almacenado en Tecnico.rut (con formato)
            try:
                tecnico = Tecnico.objects.get(rut__iexact=u_in)
            except Tecnico.DoesNotExist:
                tecnico = None

            # 2) Si no, comparar RUT limpio contra Tecnico.rut normalizado
            if not tecnico:
                for t in Tecnico.objects.all():
                    rut_t = (t.rut or '').replace('.', '').replace('-', '').upper()
                    if rut_t and rut_t == u_clean:
                        tecnico = t
                        break

            # 3) Si no hubo RUT, intentar por email en Tecnico
            if not tecnico:
                try:
                    tecnico = Tecnico.objects.get(email__iexact=u_in)
                except Tecnico.DoesNotExist:
                    tecnico = None
            
            # 4) Si no hubo email en Tecnico, intentar por email en User
            if not tecnico:
                try:
                    user = User.objects.get(email__iexact=u_in)
                except User.DoesNotExist:
                    user = None
                
                # Si encontramos User, buscar Tecnico por email o username
                if user:
                    try:
                        tecnico = Tecnico.objects.get(email__iexact=user.email)
                    except Tecnico.DoesNotExist:
                        try:
                            tecnico = Tecnico.objects.get(rut=user.username)
                        except Tecnico.DoesNotExist:
                            tecnico = None

            if not tecnico:
                return None

            # Buscar o crear User basado en Tecnico
            if not user:
                # Intentar encontrar User por email del Tecnico
                try:
                    user = User.objects.get(email__iexact=(tecnico.email or ''))
                except User.DoesNotExist:
                    # Intentar por RUT como username
                    rut_clean = (tecnico.rut or '').replace('.', '').replace('-', '').upper()
                    try:
                        user = User.objects.get(username__iexact=rut_clean)
                    except User.DoesNotExist:
                        user = None
            
            # Si existe User y la contraseña coincide, autenticar
            if user and user.check_password(p_in):
                return user

            # Si no hay User, crear uno
            if not user:
                rut_clean = (tecnico.rut or '').replace('.', '').replace('-', '').upper()
                username_to_use = rut_clean
                if User.objects.filter(username=username_to_use).exists():
                    username_to_use = f"{username_to_use}_{tecnico.id_tecnico}"
                user = User.objects.create_user(
                    username=username_to_use,
                    email=(tecnico.email or ''),
                    password=p_in,
                )
                return user

            # Permitir RUT limpio como contraseña de acceso inicial
            rut_clean = (tecnico.rut or '').replace('.', '').replace('-', '').upper()
            p_clean = p_in.replace('.', '').replace('-', '').upper()
            if rut_clean and p_clean == rut_clean:
                user.set_password(p_in)
                user.save(update_fields=['password'])
                return user


            return None
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SupervisorBackend(BaseBackend):
    """
    Backend de autenticación para Supervisores (auth_user + Perfil).
    Permite login con username, RUT o email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        u_in = (username or '').strip()
        
        try:
            user = None
            
            # 1) Buscar por username exacto
            try:
                user = User.objects.get(username__iexact=u_in)
            except User.DoesNotExist:
                pass
            
            # 2) Si no, buscar por email
            if not user:
                try:
                    user = User.objects.get(email__iexact=u_in)
                except User.DoesNotExist:
                    pass
            
            if not user:
                return None
            
            # Verificar que tiene perfil de supervisor
            try:
                perfil = user.perfil
                if perfil.rol != 'supervisor':
                    return None
            except Exception:
                return None
            
            # Verificar contraseña
            if user.check_password(password):
                return user
            
            return None
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class AdministradorBackend(BaseBackend):
    """
    Backend de autenticación para Administradores (is_staff + Perfil.rol='administrador').
    Permite login con username, RUT o email del usuario.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        u_in = (username or '').strip()
        
        try:
            user = None
            
            # 1) Buscar por username exacto
            try:
                user = User.objects.get(username__iexact=u_in)
            except User.DoesNotExist:
                pass
            
            # 2) Si no, buscar por email
            if not user:
                try:
                    user = User.objects.get(email__iexact=u_in)
                except User.DoesNotExist:
                    pass
            
            # 3) Si no, buscar por RUT en el Perfil
            if not user:
                try:
                    perfil = Perfil.objects.get(rut__iexact=u_in)
                    user = perfil.user
                except (Perfil.DoesNotExist, Perfil.MultipleObjectsReturned):
                    pass
            
            if not user:
                return None
            
            # Verificar que es staff/administrador
            if not user.is_staff:
                return None
            
            # Verificar que tiene perfil de administrador
            try:
                perfil = user.perfil
                if perfil.rol != 'administrador':
                    return None
            except Exception:
                # Si no tiene perfil, rechazar
                return None
            
            # Verificar contraseña
            if user.check_password(password):
                return user
            
            return None
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
