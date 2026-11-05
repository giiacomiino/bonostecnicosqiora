#!/bin/zsh
# Abre el visualizador de asistencia y productividad.
#   ./visualizar.sh            → usa el último datos_salida/bonos_os.json
#   ./visualizar.sh --actualizar → primero vuelve a leer Snowflake (abre login OAuth)
cd "$(dirname "$0")"
if [[ "$1" == "--actualizar" || ! -f datos_salida/bonos_os.json ]]; then
  .venv/bin/python snowflake/generar_bonos.py || exit 1
fi
PORT=8765
echo "Visualizador en http://localhost:$PORT/visualizador.html  (Ctrl+C para cerrar)"
( sleep 1; open "http://localhost:$PORT/visualizador.html" ) &
exec python3 -m http.server $PORT --bind 127.0.0.1
