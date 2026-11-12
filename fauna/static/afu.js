const foto = document.querySelector('#foto');
const chat = document.querySelector('#chat');
const imagen = foto.elements.imagen;
const historial = document.querySelector('#historial');
const estado = document.querySelector('#estado');
const mini = document.querySelector('#mini');
const borrador = document.querySelector('#borrador');
let activo = chat.dataset.activo === '1';
let ocupado = false;

function controles() {
  imagen.disabled = ocupado;
  borrador.querySelectorAll('button').forEach(b => b.disabled = ocupado);
  chat.elements.mensaje.disabled = ocupado || !activo || !borrador.hidden;
  chat.querySelector('button').disabled = chat.elements.mensaje.disabled;
}
function limpiarFoto() {
  if (mini.hasAttribute('src')) URL.revokeObjectURL(mini.src);
  mini.removeAttribute('src');
  foto.reset();
  borrador.hidden = true;
  controles();
}
imagen.onchange = () => {
  const archivo = imagen.files[0];
  if (!archivo) return limpiarFoto();
  if (archivo.size > 10 * 1024 * 1024) {
    limpiarFoto();
    estado.textContent = 'La foto supera los 10 MB. Elige una más pequeña.';
    return;
  }
  if (mini.hasAttribute('src')) URL.revokeObjectURL(mini.src);
  mini.src = URL.createObjectURL(archivo);
  borrador.hidden = false;
  estado.textContent = '';
  controles();
};
document.querySelector('#quitar').onclick = () => {
  limpiarFoto();
  estado.textContent = '';
  imagen.focus();
};

function burbuja(usuario, texto, archivo) {
  const elemento = document.createElement('article');
  elemento.className = usuario ? 'usuario' : 'afu';
  const nombre = document.createElement('b');
  nombre.textContent = usuario ? 'Tú' : 'AFU';
  elemento.append(nombre);
  if (archivo) {
    const img = document.createElement('img');
    img.alt = 'Fotografía enviada para identificar el animal';
    img.src = URL.createObjectURL(archivo);
    img.onload = () => { historial.scrollTop = historial.scrollHeight; };
    elemento.append(img);
  } else {
    const p = document.createElement('p');
    p.textContent = texto;
    elemento.append(p);
  }
  historial.append(elemento);
  historial.scrollTop = historial.scrollHeight;
  return elemento;
}

async function enviar(event) {
  event.preventDefault();
  if (ocupado) return;
  const esFoto = event.currentTarget === foto;
  const archivo = imagen.files[0];
  const pregunta = chat.elements.mensaje.value.trim();
  if (esFoto ? !archivo : !pregunta || !activo || !borrador.hidden) return;
  const headers = {'X-CSRFToken': foto.elements.csrfmiddlewaretoken.value};
  const body = esFoto ? new FormData(foto) : JSON.stringify({mensaje: pregunta});
  if (!esFoto) headers['Content-Type'] = 'application/json';
  const url = event.currentTarget.action;
  ocupado = true;
  controles();
  const enviada = esFoto ? null : burbuja(true, pregunta);
  estado.textContent = esFoto ? 'AFU está analizando tu foto…' : 'AFU está escribiendo…';
  try {
    const response = await fetch(url, {method: 'POST', headers, body});
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.mensaje || 'No se pudo completar el envío.');
    if (esFoto) {
      historial.querySelectorAll('img').forEach(img => URL.revokeObjectURL(img.src));
      historial.replaceChildren();
      burbuja(true, '', archivo);
      burbuja(false, data.mensaje);
      activo = true;
      limpiarFoto();
      chat.reset();
    } else {
      burbuja(false, data.respuesta);
      chat.reset();
    }
    estado.textContent = '';
  } catch (error) {
    enviada?.remove();
    estado.textContent = error.message + ' Puedes volver a intentarlo.';
  } finally {
    ocupado = false;
    controles();
    if (!chat.elements.mensaje.disabled) chat.elements.mensaje.focus();
  }
}
foto.onsubmit = enviar;
chat.onsubmit = enviar;
controles();
