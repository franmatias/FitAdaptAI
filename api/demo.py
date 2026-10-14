"""Generador determinista de demostración: no consulta servicios de IA."""
from math import ceil

CATALOG = {
    'mancuernas': [
        ('Sentadilla goblet', 'Sujeta la mancuerna cerca del pecho y mantén los talones apoyados.'),
        ('Press de pecho con mancuernas en el suelo', 'Baja con control hasta apoyar suavemente los brazos.'),
        ('Remo inclinado con mancuernas', 'Mantén la espalda estable y acerca los codos al cuerpo.'),
        ('Peso muerto rumano con mancuernas', 'Lleva la cadera hacia atrás sin redondear la espalda.'),
    ],
    'maquinas': [
        ('Prensa de piernas', 'Ajusta el asiento y evita bloquear las rodillas.'),
        ('Press de pecho en máquina', 'Ajusta los agarres a la altura del pecho.'),
        ('Remo en máquina', 'Mantén el torso apoyado y evita dar tirones.'),
        ('Curl femoral en máquina', 'Alinea la rodilla con el eje de la máquina.'),
    ],
    'poleas': [
        ('Sentadilla con polea baja', 'Mantén los talones apoyados y la tensión controlada.'),
        ('Press de pecho de pie en polea', 'Adopta una base estable y evita arquear la espalda.'),
        ('Remo de pie en polea', 'Acerca los codos al torso sin balancearte.'),
        ('Pull-through en polea', 'Mueve la cadera hacia atrás con la espalda estable.'),
    ],
    'barras_discos': [
        ('Peso muerto con barra desde el suelo', 'Utiliza una carga ligera y mantén la barra cerca del cuerpo.'),
        ('Press de hombros con disco', 'Sujeta el disco con firmeza y evita arquear la espalda.'),
        ('Remo con barra', 'Inclina el torso desde la cadera y evita los tirones.'),
        ('Sentadilla abrazando un disco', 'Mantén el disco cerca del pecho y baja con control.'),
    ],
    'peso_corporal': [
        ('Sentadilla al aire', 'Baja hasta una profundidad cómoda con los talones apoyados.'),
        ('Flexiones con rodillas apoyadas', 'Mantén el tronco alineado y baja con control.'),
        ('Elevaciones de brazos en W boca abajo', 'Eleva los brazos suavemente sin forzar el cuello.'),
        ('Puente de glúteos', 'Eleva la cadera sin arquear la zona lumbar.'),
    ],
}

def generate_demo(payload):
    equipment = [item.value for item in payload.equipamiento]
    goal = payload.objetivo.value
    reps, rest, seconds = {
        'hipertrofia': ('8–12', 75, 45),
        'fuerza': ('5–6', 120, 35),
        'perdida_grasa': ('12–15', 45, 50),
        'resistencia': ('15–20', 45, 60),
    }[goal]
    level = payload.nivel.value
    rpe = {'principiante': 'RPE 6', 'intermedio': 'RPE 7', 'avanzado': 'RPE 8'}[level]
    # Reserva cinco minutos de calentamiento y uno de transición por ejercicio.
    count = 4
    max_sets = {'principiante': 3, 'intermedio': 4, 'avanzado': 5}[level]
    sets = min(max_sets, max(1, ((payload.tiempo_minutos - 5) * 60 // count - 60 + rest) // (seconds + rest)))
    duration = ceil((300 + count * (sets * seconds + (sets - 1) * rest + 60)) / 60)
    exercises = []
    for i in range(count):
        name, cue = CATALOG[equipment[i % len(equipment)]][i]
        exercises.append(dict(nombre=name, series=sets, repeticiones=reps,
                              descanso_segundos=rest, rpe_sugerido=rpe, consejo_tecnico=cue))
    alternative = CATALOG[equipment[0]][3][0]
    return dict(calentamiento='5 minutos: marcha suave en el sitio, movilidad de hombros y caderas, y ensayos sin carga de los movimientos de la sesión.',
                ejercicios=exercises,
                alternativa_rapida=f'Como sustitución del primer ejercicio, prueba {alternative.lower()} con las mismas series y una intensidad cómoda. Si no queda material libre, espera a disponer de él.',
                tiempo_total_estimado=duration, modo='demo')
