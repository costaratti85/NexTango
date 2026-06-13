/**
 * Crea eventos de mantenimiento en Google Calendar basados en las tareas programadas.
 * Se ejecuta diariamente (por la noche) para generar los eventos del día siguiente.
 */
function crearEventosMantenimiento() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tareas_Programadas');
  if (!sheet) {
    Logger.log('Error: No se encontró la hoja Tareas_Programadas');
    return;
  }
  
  var data = sheet.getDataRange().getValues();
  var calendar = CalendarApp.getDefaultCalendar();
  
  var hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  
  for (var i = 1; i < data.length; i++) {
    var fila = data[i];
    var codigoActivo = fila[0];
    var codigoTarea = fila[1];
    var tarea = fila[2];
    var frecuenciaDias = fila[3];
    var responsable = fila[4];
    var ultimaEjecucion = fila[5] instanceof Date ? new Date(fila[5]) : null;
    
    if (!frecuenciaDias || frecuenciaDias <= 0) continue;
    
    var proximaFecha;
    if (ultimaEjecucion) {
      proximaFecha = new Date(ultimaEjecucion);
      proximaFecha.setDate(proximaFecha.getDate() + frecuenciaDias);
    } else {
      proximaFecha = new Date(hoy);
      proximaFecha.setDate(proximaFecha.getDate() + 1);
    }
    
    var fechaLimite = new Date(hoy);
    fechaLimite.setDate(fechaLimite.getDate() + 2);
    
    if (proximaFecha <= fechaLimite) {
      var idEvento = fila[8];
      
      if (!idEvento || idEvento.toString().trim() === '') {
        try {
          var tituloEvento = '🔧 ' + responsable + ': ' + tarea + ' [' + codigoActivo + ']';
          var fechaEvento = new Date(proximaFecha);
          var evento = calendar.createEvent(tituloEvento,
            new Date(fechaEvento.getFullYear(), fechaEvento.getMonth(), fechaEvento.getDate(), 8, 0),
            new Date(fechaEvento.getFullYear(), fechaEvento.getMonth(), fechaEvento.getDate(), 8, 30),
            {description: 'Código tarea: ' + codigoTarea + '\\nResponsable: ' + responsable + '\\nFrecuencia: cada ' + frecuenciaDias + ' días'}
          );
          evento.addPopupReminder(30);
          sheet.getRange(i + 1, 9).setValue(evento.getId());
          sheet.getRange(i + 1, 7).setValue(proximaFecha);
        } catch (e) {
          Logger.log('Error al crear evento para ' + codigoTarea + ': ' + e.toString());
        }
      }
    }
  }
}

/**
 * Marca una tarea como completada y actualiza la fecha de última ejecución.
 */
function marcarCompletadas() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Tareas_Programadas');
  var data = sheet.getDataRange().getValues();
  var calendar = CalendarApp.getDefaultCalendar();
  
  for (var i = 1; i < data.length; i++) {
    var completada = data[i][7];
    var idEvento = data[i][8];
    
    if (completada === 'S' && idEvento && idEvento.toString().trim() !== '') {
      try {
        var evento = calendar.getEventById(idEvento);
        if (evento) {
          evento.setColor(CalendarApp.EventColor.GREEN);
        }
        var hoy = new Date();
        hoy.setHours(0,0,0,0);
        sheet.getRange(i + 1, 6).setValue(hoy);
        sheet.getRange(i + 1, 8).setValue('');
        sheet.getRange(i + 1, 9).setValue('');
      } catch (e) {
        Logger.log('Error al procesar completada para ' + data[i][1] + ': ' + e.toString());
      }
    }
  }
}