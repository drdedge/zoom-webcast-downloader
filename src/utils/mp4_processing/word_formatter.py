# utils/word_formatter.py
"""
Word Document Formatter
Converts markdown to professionally formatted Word documents
"""

import io
import os
import logging
from pathlib import Path
from typing import Optional, Union
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import mistune
from htmldocx import HtmlToDocx

from ..logger_setup import setup_logger

logger = setup_logger(name = "WordDocFormatter", level=logging.INFO)


class WordDocFormatter:
    """
    Utility class for converting markdown to formatted Word documents.
    This class provides methods to create professionally formatted
    Word documents from markdown strings.
    """
    
    def __init__(self, 
                 font_name="Calibri", 
                 font_size=10, 
                 heading_font="Calibri", 
                 heading_sizes=None,
                 heading_color="#025B95",
                 table_header_bg_color="#025B95",
                 custom_table_style=True,
                 page_orientation="portrait",
                 margins=None):
        """
        Initialize the WordDocFormatter with default formatting options.
        
        Args:
            font_name (str): Default font name for body text
            font_size (int): Default font size in points for body text
            heading_font (str): Font name for headings
            heading_sizes (dict): Dictionary mapping heading levels to font sizes
            heading_color (str): Hex color code for headings
            table_header_bg_color (str): Hex color code for table header background
            custom_table_style (bool): Whether to apply custom table styling
            page_orientation (str): Page orientation ('portrait' or 'landscape')
            margins (dict): Page margins in inches for 'top', 'bottom', 'left', 'right'
        """
        self.font_name = font_name
        self.font_size = font_size
        self.heading_font = heading_font
        self.heading_sizes = heading_sizes or {'h1': 16, 'h2': 14, 'h3': 12, 'h4': 11}
        self.heading_color = heading_color
        self.table_header_bg_color = table_header_bg_color
        self.custom_table_style = custom_table_style
        self.page_orientation = page_orientation
        self.margins = margins or {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}
        self.logger = logger
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def format_table_with_custom_style(self, doc: Document):
        """
        Apply custom table formatting:
        - Header: Bold, white text, specified font, custom background color
        - Body: Specified font, black text
        - Borders: Only top and bottom (and horizontal inside borders)
        - Font size: Consistent throughout table
        
        Args:
            doc (Document): The docx Document object to be modified
        """
        # Define XML for borders and cell margins
        borders_xml = f'''
        <w:tblBorders {nsdecls('w')}>
            <w:top w:val="single" w:sz="4" w:color="auto"/>
            <w:left w:val="nil"/>
            <w:bottom w:val="single" w:sz="4" w:color="auto"/>
            <w:right w:val="nil"/>
            <w:insideH w:val="single" w:sz="4" w:color="auto"/>
            <w:insideV w:val="nil"/>
        </w:tblBorders>
        '''
        margin_xml = f'''
        <w:tcMar {nsdecls('w')}>
            <w:top w:w="70" w:type="dxa"/>
            <w:bottom w:w="70" w:type="dxa"/>
            <w:left w:w="100" w:type="dxa"/>
            <w:right w:w="100" w:type="dxa"/>
        </w:tcMar>
        '''

        # Remove # from color hex if present
        header_bg_color = self.table_header_bg_color.lstrip('#')

        for table in doc.tables:
            # Apply border settings
            table._tblPr.append(parse_xml(borders_xml))
            for row_idx, row in enumerate(table.rows):
                for cell in row.cells:
                    # Set cell margins
                    cell._element.tcPr.append(parse_xml(margin_xml))
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.name = self.font_name
                            run.font.size = Pt(self.font_size)
                            if row_idx == 0:  # Header row styling
                                run.font.bold = True
                                run.font.color.rgb = RGBColor(255, 255, 255)  # White
                            else:
                                run.font.color.rgb = RGBColor(0, 0, 0)  # Black
                    # Apply header background shading
                    if row_idx == 0:
                        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{header_bg_color}"/>')
                        cell._tc.get_or_add_tcPr().append(shading)
    
    def markdown_to_docx(self, 
                        markdown_text: str, 
                        output_filepath: Optional[Union[str, Path]] = None, 
                        reference_docx_path: Optional[Union[str, Path]] = None) -> Union[io.BytesIO, bool]:
        """
        Convert markdown text to a formatted Word document.
        
        Args:
            markdown_text (str): The markdown text to convert
            output_filepath: Path to save the output file. If None, returns a BytesIO object.
            reference_docx_path: Path to a reference docx file to use as a template
            
        Returns:
            BytesIO object containing the document if output_filepath is None,
            otherwise True on success, False on failure
        """
        try:
            # Create document from reference or new
            if reference_docx_path and Path(reference_docx_path).exists():
                doc = Document(reference_docx_path)
                self.logger.info(f"Using reference document: {reference_docx_path}")
            else:
                doc = Document()
            
            # Set page orientation and margins
            section = doc.sections[0]
            if self.page_orientation.lower() == "landscape":
                section.orientation = WD_ORIENT.LANDSCAPE
                section.page_width, section.page_height = section.page_height, section.page_width
            
            section.top_margin = Inches(self.margins['top'])
            section.bottom_margin = Inches(self.margins['bottom'])
            section.left_margin = Inches(self.margins['left'])
            section.right_margin = Inches(self.margins['right'])
            
            # Convert Markdown to HTML and then to Word
            # Ensure we get valid HTML by wrapping content in a div if needed
            html = mistune.create_markdown(plugins=['table'], escape=False)(markdown_text)
            
            # Check if the HTML doesn't start with a tag (to avoid the BeautifulSoup warning)
            if html and not html.strip().startswith('<'):
                html = f'<div>{html}</div>'
                
            # Add proper HTML structure if it's just fragments
            if html and not html.strip().startswith('<!DOCTYPE') and not html.strip().startswith('<html'):
                html = f'<html><body>{html}</body></html>'
                
            HtmlToDocx().add_html_to_document(html, doc)
            
            # Apply custom table formatting if needed
            if self.custom_table_style:
                self.format_table_with_custom_style(doc)
            
            # Set default font for paragraphs and adjust headings
            for p in doc.paragraphs:
                for run in p.runs:
                    run.font.name = self.font_name
                    run.font.size = Pt(self.font_size)
                
                if p.style.name.startswith('Heading'):
                    try:
                        level = int(p.style.name[-1])
                    except ValueError:
                        level = 1
                    
                    if level <= 4:  # Support up to h4
                        for run in p.runs:
                            run.font.name = self.heading_font
                            run.font.size = Pt(self.heading_sizes.get(f'h{level}', self.font_size))
                            run.font.bold = True
                            
                            if self.heading_color:
                                r, g, b = self._hex_to_rgb(self.heading_color)
                                run.font.color.rgb = RGBColor(r, g, b)
            
            # Return result based on output_filepath
            if output_filepath:
                output_path = Path(output_filepath)
                doc.save(str(output_path))
                self.logger.info(f"Document saved to: {output_path}")
                return True
            else:
                # Return as BytesIO
                docx_buffer = io.BytesIO()
                doc.save(docx_buffer)
                docx_buffer.seek(0)
                return docx_buffer
                
        except Exception as e:
            self.logger.error(f"Error in converting Markdown to DOCX: {e}")
            return False
            
    def markdown_to_memory(self, 
                          markdown_text: str, 
                          reference_docx_path: Optional[Union[str, Path]] = None) -> io.BytesIO:
        """
        Convert markdown text to a Word document and return as BytesIO object.
        Convenience method that calls markdown_to_docx with output_filepath=None.
        
        Args:
            markdown_text (str): The markdown text to convert
            reference_docx_path: Path to a reference docx file to use as a template
            
        Returns:
            BytesIO: BytesIO object containing the document
        """
        return self.markdown_to_docx(markdown_text, output_filepath=None, reference_docx_path=reference_docx_path)
    
    # Setters for individual properties
    def set_font(self, font_name: str, font_size: Optional[int] = None):
        """Update the default font settings"""
        self.font_name = font_name
        if font_size is not None:
            self.font_size = font_size
    
    def set_heading_style(self, font: Optional[str] = None, sizes: Optional[dict] = None, color: Optional[str] = None):
        """Update heading style settings"""
        if font is not None:
            self.heading_font = font
        if sizes is not None:
            self.heading_sizes = sizes
        if color is not None:
            self.heading_color = color
    
    def set_page_orientation(self, orientation: str):
        """Set page orientation ('portrait' or 'landscape')"""
        if orientation.lower() in ['portrait', 'landscape']:
            self.page_orientation = orientation.lower()
    
    def set_margins(self, margins: dict):
        """Set page margins in inches"""
        if isinstance(margins, dict) and all(k in margins for k in ['top', 'bottom', 'left', 'right']):
            self.margins = margins