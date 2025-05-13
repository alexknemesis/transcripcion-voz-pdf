# E:\PROJECTS\voice_test\pdf_generator.py

import os
from fpdf import FPDF
import io

class PDF(FPDF):
    font_name = 'Arial' 
    font_style_main = 'B'
    font_style_section = 'B'
    font_style_body_label = 'B'
    font_style_body_value = ''
    font_size_main = 14
    font_size_section = 11
    font_size_body_label = 9
    font_size_body_value = 9
    font_size_footer = 8
    font_size_transcript = 7
    font_size_odontogram_tooth = 8
    line_height = 5
    line_height_transcript = 4
    line_height_odontogram = 4

    def __init__(self, orientation='P', unit='mm', format='A4', font_name='Arial'):
        super().__init__(orientation, unit, format)
        self.font_name = font_name
        self.has_italic_variant = (font_name == 'Arial')
        self.has_bold_variant = (font_name == 'Arial')

    def header(self):
        style = self.font_style_main if self.has_bold_variant else ''
        self.set_font(self.font_name, style, self.font_size_main)
        self.cell(0, 8, 'Historia Clínica Odontológica (Dictado por IA)', 0, 0, 'C')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        style = 'I' if self.has_italic_variant else ''
        self.set_font(self.font_name, style, self.font_size_footer)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        style = self.font_style_section if self.has_bold_variant else ''
        self.set_font(self.font_name, style, self.font_size_section)
        self.set_fill_color(220, 220, 220)
        self.cell(0, 7, title, 0, 1, 'L', fill=True)
        self.ln(1)

    def chapter_body_field(self, label, value, indent_px=0, is_list_item_dict=False):
        if label.lower() == "odontograma completo" and isinstance(value, dict):
            if value: 
                self.render_odontograma_completo(value, indent_px_for_table=indent_px)
            else: 
                self.set_font(self.font_name, self.font_style_body_value, self.font_size_body_value)
                self.set_x(self.l_margin + indent_px)
                self.multi_cell(0, self.line_height, "(No se reportaron hallazgos en el odontograma)", 0, "L")
            return 

        if value is None or value == "" or \
           (isinstance(value, list) and not value and not is_list_item_dict) or \
           (isinstance(value, dict) and not value):
            return

        left_margin = self.l_margin
        right_margin = self.r_margin
        page_width_effective = self.w - left_margin - right_margin

        field_start_x = left_margin + indent_px
        current_y = self.get_y()

        self.set_xy(field_start_x, current_y)
        label_style = self.font_style_body_label if self.has_bold_variant else ''
        self.set_font(self.font_name, label_style, self.font_size_body_label)

        max_label_width_px = 55 
        available_for_label_value_pair = page_width_effective - indent_px
        actual_label_width_px = min(max_label_width_px, available_for_label_value_pair - 15) 
        
        if actual_label_width_px <= 0:
            self.ln(self.line_height)
            return

        y_before_multicell_label = self.get_y()
        self.multi_cell(actual_label_width_px, self.line_height, f"{label}:", 0, "L")
        y_after_multicell_label = self.get_y()

        x_for_value = field_start_x + actual_label_width_px + 1 
        width_for_value = page_width_effective - (x_for_value - left_margin)
        y_start_for_value = y_before_multicell_label

        if width_for_value < 10: 
            self.set_xy(field_start_x, y_after_multicell_label)
            x_for_value = field_start_x
            width_for_value = page_width_effective - indent_px
            y_start_for_value = y_after_multicell_label
        
        if width_for_value <= 0:
            self.set_y(y_after_multicell_label)
            self.ln(self.line_height)
            return

        self.set_xy(x_for_value, y_start_for_value)
        self.set_font(self.font_name, self.font_style_body_value, self.font_size_body_value)

        if isinstance(value, list):
            for i, item in enumerate(value):
                item_x_start = x_for_value + (5 if not is_list_item_dict else 0) 
                item_width = page_width_effective - (item_x_start - left_margin)
                self.set_x(item_x_start)
                if item_width <= 0: continue

                if isinstance(item, dict): 
                    item_text_parts = [f"{k.replace('_',' ').capitalize()}: {v_item}" for k, v_item in item.items() if v_item]
                    self.multi_cell(item_width, self.line_height, f"- {'; '.join(item_text_parts)}", 0, "L")
                else: 
                    self.multi_cell(item_width, self.line_height, f"- {str(item)}", 0, "L")
        elif isinstance(value, dict): 
            self.set_xy(field_start_x, y_after_multicell_label)
            for k_dict, v_dict in value.items():
                self.chapter_body_field(k_dict.replace('_',' ').capitalize(), v_dict, indent_px=indent_px + 5)
        else: 
            self.multi_cell(width_for_value, self.line_height, str(value), 0, "L")
        
        y_after_value = self.get_y()
        self.set_y(max(y_after_multicell_label, y_after_value))

    def render_odontograma_completo(self, odontograma_data: dict, indent_px_for_table: float):
        if not odontograma_data:
            return

        self.ln(1) 
        
        left_margin = self.l_margin
        right_margin = self.r_margin
        
        table_start_x = left_margin + indent_px_for_table
        table_width_available = self.w - right_margin - table_start_x

        col_widths = { "pieza": 15, "diagnostico": 60, "plan": 60, "notas": 0 }
        
        if table_width_available < (col_widths["pieza"] + col_widths["diagnostico"] + col_widths["plan"] + 10):
            table_start_x = left_margin
            table_width_available = self.w - left_margin - right_margin
            print(f"DEBUG: Odontograma movido al margen izquierdo. Ancho disponible: {table_width_available}")

        col_widths["notas"] = max(15, table_width_available - (col_widths["pieza"] + col_widths["diagnostico"] + col_widths["plan"] + 3))

        header_style = 'B' if self.has_bold_variant else ''
        self.set_font(self.font_name, header_style, self.font_size_odontogram_tooth)
        
        self.set_x(table_start_x)
        self.cell(col_widths["pieza"], self.line_height_odontogram, "Pieza", 1, 0, 'C')
        self.cell(col_widths["diagnostico"], self.line_height_odontogram, "Diagnóstico/Hallazgo", 1, 0, 'C')
        self.cell(col_widths["plan"], self.line_height_odontogram, "Plan Tratamiento", 1, 0, 'C')
        self.cell(col_widths["notas"], self.line_height_odontogram, "Notas", 1, 1, 'C')

        self.set_font(self.font_name, '', self.font_size_odontogram_tooth)
        
        def fdi_sort_key(pieza_str):
            try:
                num_str = str(pieza_str).split('.')[0] 
                num = int(num_str)
                cuadrante = num // 10
                diente = num % 10
                cuadrante_orden = {1:1, 2:2, 4:3, 3:4} 
                return (cuadrante_orden.get(cuadrante, 9), diente if cuadrante in [1,4] else -diente)
            except ValueError: return (99, pieza_str)

        sorted_piezas = sorted(odontograma_data.keys(), key=fdi_sort_key)

        for pieza_num_str in sorted_piezas:
            pieza_info = odontograma_data[pieza_num_str]
            if not pieza_info or not isinstance(pieza_info, dict): continue

            diag = pieza_info.get("diagnostico_hallazgo", "-") or "-"
            plan = pieza_info.get("plan_tratamiento_sugerido", "-") or "-"
            notas = pieza_info.get("notas_adicionales", "-") or "-"

            y_start_row = self.get_y()
            if y_start_row > self.h - self.b_margin - (self.line_height_odontogram * 4): 
                self.add_page()
                self.set_font(self.font_name, header_style, self.font_size_odontogram_tooth)
                self.set_x(table_start_x)
                self.cell(col_widths["pieza"], self.line_height_odontogram, "Pieza", 1, 0, 'C')
                self.cell(col_widths["diagnostico"], self.line_height_odontogram, "Diagnóstico/Hallazgo", 1, 0, 'C')
                self.cell(col_widths["plan"], self.line_height_odontogram, "Plan Tratamiento", 1, 0, 'C')
                self.cell(col_widths["notas"], self.line_height_odontogram, "Notas", 1, 1, 'C')
                self.set_font(self.font_name, '', self.font_size_odontogram_tooth)
                y_start_row = self.get_y()

            max_h_in_row = self.line_height_odontogram 

            self.set_xy(table_start_x, y_start_row)
            self.multi_cell(col_widths["pieza"], self.line_height_odontogram, str(pieza_num_str), 1, "C")
            max_h_in_row = max(max_h_in_row, self.get_y() - y_start_row)

            self.set_xy(table_start_x + col_widths["pieza"], y_start_row)
            self.multi_cell(col_widths["diagnostico"], self.line_height_odontogram, diag, 1, "L")
            max_h_in_row = max(max_h_in_row, self.get_y() - y_start_row)

            self.set_xy(table_start_x + col_widths["pieza"] + col_widths["diagnostico"], y_start_row)
            self.multi_cell(col_widths["plan"], self.line_height_odontogram, plan, 1, "L")
            max_h_in_row = max(max_h_in_row, self.get_y() - y_start_row)

            self.set_xy(table_start_x + col_widths["pieza"] + col_widths["diagnostico"] + col_widths["plan"], y_start_row)
            self.multi_cell(col_widths["notas"], self.line_height_odontogram, notas, 1, "L")
            max_h_in_row = max(max_h_in_row, self.get_y() - y_start_row)
            
            self.set_y(y_start_row + max_h_in_row)


def create_pdf_from_json(data: dict) -> bytes:
    font_dir = os.path.dirname(os.path.abspath(__file__))
    dejavu_regular_path = os.path.join(font_dir, "DejaVuSans.ttf")
    dejavu_bold_path = os.path.join(font_dir, "DejaVuSans-Bold.ttf")
    dejavu_italic_path = os.path.join(font_dir, "DejaVuSans-Oblique.ttf")

    active_font_name = 'Arial'
    pdf = PDF(font_name=active_font_name)
    
    if os.path.exists(dejavu_regular_path):
        try:
            pdf.add_font('DejaVu', '', dejavu_regular_path, uni=True)
            active_font_name = 'DejaVu'
            pdf.font_name = active_font_name
            print("Fuente DejaVu (Regular) registrada.")

            pdf.has_bold_variant = False
            if os.path.exists(dejavu_bold_path):
                pdf.add_font('DejaVu', 'B', dejavu_bold_path, uni=True)
                pdf.has_bold_variant = True
                print("Fuente DejaVu (Bold) registrada.")
            else:
                pdf.add_font('DejaVu', 'B', dejavu_regular_path, uni=True)
                print("Advertencia: DejaVuSans-Bold.ttf no encontrada, usando regular para Bold.")

            pdf.has_italic_variant = False
            if os.path.exists(dejavu_italic_path):
                pdf.add_font('DejaVu', 'I', dejavu_italic_path, uni=True)
                pdf.has_italic_variant = True
                print("Fuente DejaVu (Italic) registrada.")
            else:
                pdf.add_font('DejaVu', 'I', dejavu_regular_path, uni=True)
                print("Advertencia: DejaVuSans-Oblique.ttf no encontrada, usando regular para Italic.")
        except Exception as e:
            print(f"Error al registrar fuentes DejaVu: {e}. Usando Arial.")
            active_font_name = 'Arial'
            pdf.font_name = active_font_name
            pdf.has_bold_variant = True 
            pdf.has_italic_variant = True
    else:
        print("Advertencia: DejaVuSans.ttf no encontrada. Usando Arial.")
        pdf.has_bold_variant = True
        pdf.has_italic_variant = True

    pdf.add_page() 
    pdf.set_font(pdf.font_name, '', pdf.font_size_body_value) 
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- Función auxiliar para escribir secciones ---
    def write_pdf_section(title, fields_data, is_last_section_arg=False): 
        has_data = False
        if isinstance(fields_data, list):
            has_data = any(field_info[1] for field_info in fields_data if len(field_info) > 1 and field_info[1])
        elif isinstance(fields_data, dict) and fields_data: 
            has_data = True
        elif isinstance(fields_data, dict) and not fields_data and title.lower() == "odontograma completo": 
            has_data = True 

        if not has_data:
            return

        min_height_for_section = pdf.font_size_section * 0.352778 * 1.5 + pdf.font_size_body_value * 0.352778 * 1.5 + 3 
        if pdf.get_y() + min_height_for_section > (pdf.h - pdf.b_margin):
            pdf.add_page()

        pdf.chapter_title(title)
        if isinstance(fields_data, list):
            for field_info in fields_data:
                label, value = field_info[0], field_info[1]
                is_list_item_dict_flag = field_info[2] if len(field_info) > 2 else False
                pdf.chapter_body_field(label, value, is_list_item_dict=is_list_item_dict_flag)
        elif isinstance(fields_data, dict): 
             pdf.chapter_body_field(title, fields_data) 

    # --- Definir y escribir secciones ---
    main_content_sections = []
    main_content_sections.append(("Información General del Dictado", [
        ("Paciente Identificado", data.get("paciente_identificador_mencionado_opcional")),
        ("Fecha/Hora Dictado (Aprox.)", data.get("fecha_hora_dictado_aproximada"))
    ]))
    main_content_sections.append(("Motivo de Consulta y Enfermedad Actual", [
        ("Queja Principal", data.get("queja_principal_detectada")),
        ("Historia Enfermedad Actual", data.get("historia_enfermedad_actual_detectada"))
    ]))
    if data.get("antecedentes_medicos_relevantes_detectados"):
        main_content_sections.append(("Antecedentes Médicos Relevantes", [
            ("Antecedentes", data.get("antecedentes_medicos_relevantes_detectados"))
        ]))
    main_content_sections.append(("Examen Clínico", [
        ("Hallazgos Examen Extraoral", data.get("hallazgos_examen_extraoral_detectados")),
        ("Hallazgos Examen Intraoral General", data.get("hallazgos_examen_intraoral_general_detectados"))
    ]))
    
    odontograma_data = data.get("odontograma_completo")
    if odontograma_data is not None: 
        main_content_sections.append(("Odontograma Completo", odontograma_data))
    
    if data.get("diagnosticos_sugeridos_ia"):
        main_content_sections.append(("Diagnósticos Generales Sugeridos por IA", [
            ("Diagnósticos", data.get("diagnosticos_sugeridos_ia"))
        ]))
    if data.get("procedimientos_realizados_sesion_detectados"):
        main_content_sections.append(("Procedimientos Realizados en Sesión", [
            ("Procedimientos", data.get("procedimientos_realizados_sesion_detectados"), True)
        ]))
    
    indic_plan_fields = []
    if data.get("indicaciones_postoperatorias_detectadas"): indic_plan_fields.append(("Indicaciones Postoperatorias", data.get("indicaciones_postoperatorias_detectadas")))
    if data.get("medicacion_recetada_detectada"): indic_plan_fields.append(("Medicación Recetada", data.get("medicacion_recetada_detectada")))
    if data.get("plan_proxima_cita_detectado"): indic_plan_fields.append(("Plan Próxima Cita", data.get("plan_proxima_cita_detectado")))
    if indic_plan_fields:
        main_content_sections.append(("Indicaciones y Planificación", indic_plan_fields))

    observaciones_generales = data.get("observaciones_generales_dictadas")
    if observaciones_generales:
        main_content_sections.append(("Observaciones Generales Dictadas", [
            ("Observaciones", observaciones_generales)
        ]))

    # Escribir secciones principales
    num_main_sections = len(main_content_sections)
    original_transcript = data.get("texto_transcrito_original") 

    for i, (title, fields_or_dict) in enumerate(main_content_sections):
        is_last = (i == num_main_sections - 1) and not original_transcript
        write_pdf_section(title, fields_or_dict, is_last_section_arg=is_last) 
        
        if not is_last:
             pdf.ln(2)

    if original_transcript:
        min_height_for_transcript_title = pdf.font_size_section * 0.352778 * 1.5 + 3 
        if pdf.get_y() + min_height_for_transcript_title > (pdf.h - pdf.b_margin):
            pdf.add_page()
        elif num_main_sections > 0 : 
             pdf.ln(3) 

        pdf.chapter_title("Transcripción Original Completa del Dictado")
        style = '' 
        pdf.set_font(pdf.font_name, style, pdf.font_size_transcript)
        pdf.multi_cell(0, pdf.line_height_transcript, original_transcript, 0, "L")
    
    # Generar PDF en memoria
    pdf_output = pdf.output(dest='S')
    # Verificar si el resultado ya es un bytearray o necesita ser codificado
    if isinstance(pdf_output, bytearray) or isinstance(pdf_output, bytes):
        pdf_bytes = pdf_output
    else:
        pdf_bytes = pdf_output.encode('latin1')
    return pdf_bytes