"""Interfaz Tkinter de escritorio para RF-02 a RF-17 (sin dependencias externas)."""
from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import filedialog, messagebox, ttk
from solucion.datos import auditoria_repo
from solucion.negocio import estudiantes, salas, reservaciones, reportes, panel
from solucion.modelos.sala import ESTADO_DISPONIBLE, ESTADO_FUERA_SERVICIO


class Aplicacion(tk.Tk):
    """Pantallas integradas; ninguna sentencia SQL se encuentra en la interfaz."""
    def __init__(self):
        super().__init__()
        self.title("Sistema de reservación de salas | Grupo 2")
        self.geometry("1140x760")
        self.minsize(950,680)
        self._cambios_pendientes=False
        self.configure(bg="#f3f6fa")
        self._estilo()
        self.protocol("WM_DELETE_WINDOW",self._salir)
        self._cabecera()
        self.tabs=ttk.Notebook(self)
        self.tabs.pack(fill="both",expand=True,padx=16,pady=(0,12))
        self._tab_panel()
        self._tab_estudiantes()
        self._tab_salas()
        self._tab_reservas()
        self._tab_recurrencias()
        self._tab_reportes()
        self._tab_auditoria()
        # RF-10: identificar datos editados que aún no han sido confirmados.
        for grupo in (self.e, self.s, self.r, self.rec):
            for variable in grupo.values():
                variable.trace_add("write", self._marcar_pendiente)
        self.tabs.bind("<<NotebookTabChanged>>",lambda e: self.actualizar_todo())
        self._status=tk.StringVar(value="Listo. Base SQLite inicializada.")
        ttk.Label(self,textvariable=self._status,style="Estado.TLabel").pack(fill="x",padx=16,pady=(0,8))
        self.actualizar_todo()

    def _estilo(self):
        s=ttk.Style(self)
        try:s.theme_use("clam")
        except tk.TclError:pass
        s.configure("TFrame",background="#ffffff")
        s.configure("TLabel",background="#ffffff",foreground="#27364c",font=("Segoe UI",10))
        s.configure("TNotebook",background="#f3f6fa",borderwidth=0)
        s.configure("TNotebook.Tab",padding=(16,9),font=("Segoe UI",10,"bold"))
        s.map("TNotebook.Tab",background=[("selected","#ffffff")],foreground=[("selected","#1263b5")])
        s.configure("TButton",padding=7,font=("Segoe UI",9))
        s.configure("Accion.TButton",background="#1164b5",foreground="white")
        s.map("Accion.TButton",background=[("active","#084a87")])
        s.configure("Treeview",rowheight=27,font=("Segoe UI",9),background="white",fieldbackground="white")
        s.configure("Treeview.Heading",font=("Segoe UI",9,"bold"),padding=7)
        s.configure("Titulo.TLabel",font=("Segoe UI",14,"bold"),foreground="#173f68")
        s.configure("Estado.TLabel",background="#f3f6fa",foreground="#435065",font=("Segoe UI",9))
        s.configure("Resumen.TLabel",font=("Segoe UI",11,"bold"))
        s.configure("TLabelframe",background="white")
        s.configure("TLabelframe.Label",background="white",font=("Segoe UI",10,"bold"))

    def _cabecera(self):
        encabezado=tk.Frame(self,bg="#123f70",height=76)
        encabezado.pack(fill="x",pady=(0,12))
        encabezado.pack_propagate(False)
        tk.Label(encabezado,text="Reservación de salas de estudio",font=("Segoe UI",19,"bold"),
                 bg="#123f70",fg="white").pack(anchor="w",padx=23,pady=(11,0))
        tk.Label(encabezado,text="Grupo 2 · Gestión y trazabilidad · Fase 6",font=("Segoe UI",10),
                 bg="#123f70",fg="#c9e2ff").pack(anchor="w",padx=24)

    def _hoja(self,nombre,titulo,descripcion):
        hoja=ttk.Frame(self.tabs,padding=14)
        self.tabs.add(hoja,text=nombre)
        ttk.Label(hoja,text=titulo,style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(hoja,text=descripcion).pack(anchor="w",pady=(2,13))
        return hoja

    def _formulario(self,padre,campos):
        variables={}
        zona=ttk.Frame(padre)
        zona.pack(fill="x",pady=(0,8))
        for i,(clave,etiqueta,valor) in enumerate(campos):
            renglon=i//3; columna=i%3
            bloque=ttk.Frame(zona)
            bloque.grid(row=renglon,column=columna,sticky="ew",padx=(0,12),pady=5)
            ttk.Label(bloque,text=etiqueta).pack(anchor="w")
            var=tk.StringVar(value=valor)
            ttk.Entry(bloque,textvariable=var,width=26).pack(fill="x")
            variables[clave]=var
        for i in range(3):zona.columnconfigure(i,weight=1)
        return variables

    def _botones(self,padre,acciones):
        bar=ttk.Frame(padre)
        bar.pack(fill="x",pady=(4,12))
        for i,(etiqueta,funcion) in enumerate(acciones):
            ttk.Button(bar,text=etiqueta,command=funcion,style="Accion.TButton" if i==0 else "TButton").pack(side="left",padx=(0,8))

    def _arbol(self,padre,columnas,altura=9):
        cont=ttk.Frame(padre)
        cont.pack(fill="both",expand=True)
        arbol=ttk.Treeview(cont,columns=[c[0] for c in columnas],show="headings",height=altura,selectmode="browse")
        for clave,encabezado,ancho in columnas:
            arbol.heading(clave,text=encabezado)
            arbol.column(clave,width=ancho,anchor="w",stretch=True)
        y=ttk.Scrollbar(cont,orient="vertical",command=arbol.yview)
        arbol.configure(yscrollcommand=y.set)
        arbol.pack(side="left",fill="both",expand=True)
        y.pack(side="right",fill="y")
        return arbol

    def _poner(self,tabla,filas):
        tabla.delete(*tabla.get_children())
        for fila in filas:
            tabla.insert("","end",values=fila)

    def _seleccion(self,tabla):
        seleccion=tabla.selection()
        return tabla.item(seleccion[0],"values") if seleccion else None

    def _marcar_pendiente(self, *_args):
        self._cambios_pendientes=True

    def _resultado(self,r):
        self._status.set(r.mensaje)
        if r.exito:
            self._cambios_pendientes=False
            messagebox.showinfo("Operación completada",r.mensaje,parent=self)
            self.actualizar_todo()
        else:
            messagebox.showwarning("Operación no realizada",r.mensaje,parent=self)
        return r.exito

    def _numero(self,var):
        try:return int(var.get())
        except (ValueError,TypeError):return None

    def _tab_estudiantes(self):
        hoja=self._hoja("Estudiantes","Gestión de estudiantes","RF-02, RF-03 y RF-11 · Registrar, consultar, editar y cambiar el estado")
        self.e=self._formulario(hoja,[("carne","Carné (10 caracteres)",""),("nombre","Nombre completo",""),
                                      ("correo","Correo electrónico",""),("activo","Estado (activo/inactivo)","activo")])
        self._botones(hoja,[("Registrar",self._e_registrar),("Guardar cambios",self._e_modificar),("Actualizar lista",self._actualizar_estudiantes)])
        self.te=self._arbol(hoja,[("carne","Carné",130),("nombre","Nombre",230),("correo","Correo",280),("estado","Estado",110)])
        self.te.bind("<<TreeviewSelect>>",lambda e:self._cargar_estudiante())

    def _cargar_estudiante(self):
        v=self._seleccion(self.te)
        if v:
            for k,x in zip(("carne","nombre","correo","activo"),v):self.e[k].set(x)
            # El carné del registro seleccionado es inmutable.

    def _e_registrar(self):
        self._resultado(estudiantes.registrar_estudiante(self.e["carne"].get(),self.e["nombre"].get(),self.e["correo"].get()))

    def _e_modificar(self):
        v=self._seleccion(self.te)
        if not v:messagebox.showwarning("Selección","Seleccione un estudiante para modificar.",parent=self);return
        if self.e["carne"].get().upper()!=v[0].upper():
            messagebox.showwarning("Carné protegido","El carné no puede modificarse.",parent=self);return
        if not messagebox.askyesno("Confirmación","¿Desea guardar los cambios del estudiante?",parent=self):return
        estado=self.e["activo"].get().strip().lower()
        if estado not in ("activo","inactivo"):
            messagebox.showwarning("Estado","Escriba activo o inactivo.",parent=self);return
        self._resultado(estudiantes.modificar_estudiante(v[0],self.e["nombre"].get(),self.e["correo"].get(),estado=="activo"))

    def _actualizar_estudiantes(self):
        r=estudiantes.consultar_estudiantes()
        if r.exito:self._poner(self.te,[(x.carne,x.nombre,x.correo,"activo" if x.activo else "inactivo") for x in r.datos])

    def _tab_salas(self):
        hoja=self._hoja("Salas","Gestión de salas","RF-04 y RF-12 · La capacidad no puede afectar reservaciones activas futuras")
        self.s=self._formulario(hoja,[("codigo","Código de sala",""),("nombre","Nombre de sala",""),
                                      ("capacidad","Capacidad","4"),("estado","Estado (disponible/fuera_de_servicio)","disponible")])
        self._botones(hoja,[("Registrar sala",self._s_registrar),("Guardar cambios",self._s_modificar),("Actualizar",self._actualizar_salas)])
        self.ts=self._arbol(hoja,[("codigo","Código",120),("nombre","Sala",300),("capacidad","Capacidad",125),("estado","Estado",190)])
        self.ts.bind("<<TreeviewSelect>>",lambda e:self._cargar_sala())

    def _cargar_sala(self):
        v=self._seleccion(self.ts)
        if v:
            for k,x in zip(("codigo","nombre","capacidad","estado"),v):self.s[k].set(x)

    def _s_registrar(self):
        self._resultado(salas.registrar_sala(self.s["codigo"].get(),self.s["nombre"].get(),
                  self._numero(self.s["capacidad"]),self.s["estado"].get().strip()))

    def _s_modificar(self):
        v=self._seleccion(self.ts)
        if not v:messagebox.showwarning("Selección","Seleccione una sala.",parent=self);return
        if self.s["codigo"].get().upper()!=v[0].upper():
            messagebox.showwarning("Código protegido","El código de sala no puede modificarse.",parent=self);return
        if not messagebox.askyesno("Confirmación","¿Guardar cambios de la sala?",parent=self):return
        self._resultado(salas.modificar_sala(v[0],self.s["nombre"].get(),self._numero(self.s["capacidad"]),self.s["estado"].get().strip()))

    def _actualizar_salas(self):
        r=salas.consultar_salas()
        if r.exito:self._poner(self.ts,[(x.codigo,x.nombre,x.capacidad,x.estado) for x in r.datos])

    def _tab_reservas(self):
        hoja=self._hoja("Reservaciones","Reservaciones y disponibilidad","RF-05 a RF-09 y RF-13 · Creación, edición, búsqueda y cancelación")
        manana=(date.today()+timedelta(days=1)).isoformat()
        self.r=self._formulario(hoja,[("id","ID para editar/cancelar",""),("carne","Carné","A001234567"),
                          ("codigo","Sala","S01"),("fecha","Fecha AAAA-MM-DD",manana),
                          ("hora","Hora HH:MM","10:00"),("duracion","Duración (1 o 2)","1"),
                          ("personas","Personas","2")])
        self._botones(hoja,[("Crear reservación",self._r_crear),("Consultar disponibilidad",self._r_disponibilidad),
                           ("Modificar seleccionada",self._r_modificar),("Cancelar seleccionada",self._r_cancelar),
                           ("Buscar por carné",self._r_buscar),("Ver historial",self._actualizar_reservas)])
        self.tr=self._arbol(hoja,self._columnas_reservas())
        self.tr.bind("<<TreeviewSelect>>",lambda e:self._cargar_reserva())

    @staticmethod
    def _columnas_reservas():
        return [("id","ID",85),("carne","Carné",112),("sala","Sala",65),("fecha","Fecha",108),
                ("hora","Inicio",73),("duracion","Horas",62),("cantidad","Personas",80),
                ("estado","Estado",85),("serie","Serie",90)]

    @staticmethod
    def _filas_reserva(rs):
        return [(x.id,x.carne_estudiante,x.codigo_sala,x.fecha,x.hora_inicio,x.duracion,
                 x.cantidad_personas,x.estado,x.serie_id or "") for x in rs]

    def _cargar_reserva(self):
        v=self._seleccion(self.tr)
        if v:
            for k,x in zip(("id","carne","codigo","fecha","hora","duracion","personas"),v):self.r[k].set(x)

    def _datos_reservacion(self):
        return (self.r["carne"].get(),self.r["codigo"].get(),self.r["fecha"].get(),
                self.r["hora"].get(),self._numero(self.r["duracion"]),self._numero(self.r["personas"]))

    def _r_crear(self):self._resultado(reservaciones.crear_reservacion(*self._datos_reservacion()))

    def _r_disponibilidad(self):
        r=reservaciones.consultar_disponibilidad(self.r["codigo"].get(),self.r["fecha"].get(),
                                 self.r["hora"].get(),self._numero(self.r["duracion"]))
        self._resultado(r)

    def _r_modificar(self):
        v=self._seleccion(self.tr)
        if not v:messagebox.showwarning("Selección","Seleccione una reservación.",parent=self);return
        if not messagebox.askyesno("Confirmación","¿Modificar la reservación seleccionada?",parent=self):return
        self._resultado(reservaciones.modificar_reservacion(v[0],self.r["codigo"].get(),self.r["fecha"].get(),
                                    self.r["hora"].get(),self._numero(self.r["duracion"]),self._numero(self.r["personas"])))

    def _r_cancelar(self):
        v=self._seleccion(self.tr)
        if not v:messagebox.showwarning("Selección","Seleccione una reservación.",parent=self);return
        if messagebox.askyesno("Confirmar cancelación",f"¿Cancelar reservación {v[0]}?",parent=self):
            self._resultado(reservaciones.cancelar_reservacion(v[0]))

    def _r_buscar(self):
        r=reservaciones.buscar_reservaciones_estudiante(self.r["carne"].get())
        if not r.exito or not r.datos:self._resultado(r)
        else:self._poner(self.tr,self._filas_reserva(r.datos));self._status.set(r.mensaje)

    def _actualizar_reservas(self):
        r=reservaciones.consultar_reservaciones()
        if r.exito:self._poner(self.tr,self._filas_reserva(r.datos))

    def _tab_recurrencias(self):
        hoja=self._hoja("Recurrencias","Series de reservaciones","RF-14 · Generar semanalmente y cancelar una ocurrencia o todas las futuras")
        self.rec=self._formulario(hoja,[("carne","Carné","A001234567"),("codigo","Sala","S01"),
             ("fecha","Fecha de inicio",(date.today()+timedelta(days=2)).isoformat()),
             ("hora","Hora de inicio","10:00"),("duracion","Duración","1"),
             ("personas","Personas","2"),("semanas","Ocurrencias (2–8)","2"),
             ("id","ID desde el cual cancelar","R0001")])
        self._botones(hoja,[("Crear serie",self._rec_crear),("Cancelar ocurrencia",self._rec_cancelar_una),
                           ("Cancelar desde ocurrencia",self._rec_cancelar_futuras),("Actualizar",self._actualizar_series)])
        ttk.Label(hoja,text="RN-11: cada ocurrencia cuenta para el máximo de tres reservas activas.").pack(anchor="w",pady=(0,8))
        self.trec=self._arbol(hoja,self._columnas_reservas())
        self.trec.bind("<<TreeviewSelect>>",lambda e:self.rec["id"].set((self._seleccion(self.trec) or [""])[0]))

    def _rec_crear(self):
        datos=(self.rec["carne"].get(),self.rec["codigo"].get(),self.rec["fecha"].get(),
               self.rec["hora"].get(),self._numero(self.rec["duracion"]),
               self._numero(self.rec["personas"]),self._numero(self.rec["semanas"]))
        vista=reservaciones.previsualizar_serie_semanal(*datos)
        if not vista.exito:self._resultado(vista);return
        detalle="\n".join(f"{x['numero']}. {x['fecha']} — {x['conflicto'] or 'disponible'}" for x in vista.datos)
        if any(x['conflicto'] for x in vista.datos):
            messagebox.showwarning("Conflictos de la serie","Conflictos detectados:\n"+detalle,parent=self)
            return
        if not messagebox.askyesno("Confirmar serie","Resumen de ocurrencias:\n"+detalle+"\n\n¿Guardar la serie?",parent=self):return
        self._resultado(reservaciones.crear_serie_semanal(*datos))

    def _rec_cancelar_una(self):
        if messagebox.askyesno("Confirmación","¿Cancelar únicamente esta ocurrencia?",parent=self):
            self._resultado(reservaciones.cancelar_reservacion(self.rec["id"].get()))

    def _rec_cancelar_futuras(self):
        if messagebox.askyesno("Confirmación","¿Cancelar esta ocurrencia y las posteriores de su serie?",parent=self):
            self._resultado(reservaciones.cancelar_ocurrencias_futuras(self.rec["id"].get()))

    def _actualizar_series(self):
        r=reservaciones.consultar_reservaciones()
        if r.exito:self._poner(self.trec,self._filas_reserva([x for x in r.datos if x.serie_id]))

    def _tab_panel(self):
        hoja=self._hoja("Panel","Panel de control","RF-15 · Ocupación por sala y próximas reservaciones")
        self.pnl_text=tk.StringVar(value="Sin datos")
        ttk.Label(hoja,textvariable=self.pnl_text,style="Resumen.TLabel").pack(anchor="w",pady=(0,8))
        filtro=ttk.LabelFrame(hoja,text="Filtros combinados",padding=8)
        filtro.pack(fill="x",pady=(0,10))
        self.filtro=self._formulario(filtro,[("desde","Desde AAAA-MM-DD",""),("hasta","Hasta AAAA-MM-DD",""),
               ("sala","Sala",""),("estado","Estado activa/cancelada",""),("carne","Carné"," ")])
        self._botones(hoja,[("Aplicar filtros",self._p_filtrar),("Limpiar filtros",self._p_limpiar),("Actualizar panel",self._actualizar_panel)])
        separacion=ttk.Panedwindow(hoja,orient="vertical")
        separacion.pack(fill="both",expand=True)
        area1=ttk.LabelFrame(separacion,text="Reservaciones resultantes",padding=7)
        area2=ttk.LabelFrame(separacion,text="Ocupación por sala (reservas activas del día)",padding=7)
        separacion.add(area1,weight=3);separacion.add(area2,weight=1)
        self.tp=self._arbol(area1,self._columnas_reservas(),altura=7)
        self.tocup=self._arbol(area2,[("codigo","Código",110),("sala","Sala",275),
                       ("capacidad","Capacidad",110),("hoy","Reservas hoy",135)],altura=4)

    def _p_filtrar(self):
        args={k:v.get().strip() for k,v in self.filtro.items()}
        r=panel.filtrar(args["desde"] or None,args["hasta"] or None,args["sala"] or None,
                         args["estado"] or None,args["carne"] or None)
        if r.exito:self._poner(self.tp,self._filas_reserva(r.datos));self._status.set(r.mensaje)
        else:self._resultado(r)

    def _p_limpiar(self):
        for v in self.filtro.values():v.set("")
        self._actualizar_panel()

    def _actualizar_panel(self):
        r=panel.resumen()
        if not r.exito:return
        d=r.datos
        self.pnl_text.set(f"Reservaciones activas hoy: {d['reservas_hoy']}   |   Próximas reservaciones: {len(d['proximas'])} (máximo 15 mostradas)")
        self._poner(self.tocup,[(x["codigo"],x["nombre"],x["capacidad"],x["reservas_hoy"]) for x in d["ocupacion"]])
        self._poner(self.tp,self._filas_reserva(d["proximas"]))

    def _tab_reportes(self):
        hoja=self._hoja("Reportes","Generar y exportar reportes","RF-16 · Fechas obligatorias, CSV UTF-8 y salida sin archivos parciales")
        hoy=date.today()
        self.rep=self._formulario(hoja,[("desde","Fecha inicial",hoy.isoformat()),
                        ("hasta","Fecha final",(hoy+timedelta(days=30)).isoformat())])
        self._botones(hoja,[("Previsualizar",self._rep_previsualizar),("Exportar CSV",self._rep_exportar)])
        self.trep=self._arbol(hoja,[("id","ID",80),("carne","Carné",120),("estudiante","Estudiante",190),
          ("sala","Sala",190),("fecha","Fecha",105),("inicio","Inicio",65),("fin","Fin",65),
          ("personas","Personas",65),("estado","Estado",100)])

    def _rep_previsualizar(self):
        r=reportes.generar_reporte(self.rep["desde"].get(),self.rep["hasta"].get())
        if r.exito:self._poner(self.trep,r.datos);self._status.set(r.mensaje)
        else:self._resultado(r)

    def _rep_exportar(self):
        antes=reportes.generar_reporte(self.rep["desde"].get(),self.rep["hasta"].get())
        if not antes.exito:self._resultado(antes);return
        ruta=filedialog.asksaveasfilename(parent=self,title="Guardar reporte",defaultextension=".csv",
                                        filetypes=[("Archivo CSV","*.csv")])
        if not ruta:self._status.set("Exportación cancelada; no se creó ningún archivo.");return
        self._resultado(reportes.exportar_csv(self.rep["desde"].get(),self.rep["hasta"].get(),ruta))

    def _tab_auditoria(self):
        hoja=self._hoja("Auditoría","Historial de auditoría","RF-17 · Registro de cambios de solo lectura (sin edición desde la interfaz)")
        self._botones(hoja,[("Actualizar historial",self._actualizar_auditoria)])
        self.ta=self._arbol(hoja,[("id","ID",80),("fecha","Fecha / hora",185),("accion","Acción",130),
                                      ("entidad","Entidad",140),("ident","Identificador",160),("detalle","Detalle",260)])

    def _actualizar_auditoria(self):
        try:
            datos=auditoria_repo.listar()
            self._poner(self.ta,[(x["id"],x["fecha_hora"],x["tipo_accion"],x["entidad"],
                                  x["identificador"],x["detalle"] or "") for x in datos])
        except Exception:
            self._status.set("No fue posible consultar el historial de auditoría.")

    def actualizar_todo(self):
        """Actualizar al completar operación; protege actualización durante construcción."""
        for nombre in ("_actualizar_estudiantes","_actualizar_salas","_actualizar_reservas",
                       "_actualizar_series","_actualizar_panel","_actualizar_auditoria"):
            if nombre=="_actualizar_panel" and not hasattr(self,"tp"):continue
            metodo=getattr(self,nombre,None)
            if metodo:metodo()

    def _salir(self):
        if self._cambios_pendientes:
            if not messagebox.askyesno("Cerrar","Hay cambios sin guardar. ¿Desea salir?",parent=self):return
        self.destroy()
