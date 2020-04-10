from sphinx.writers.latex import LaTeXTranslator

class CustomLaTeXTranslator(LaTeXTranslator):
    
    def escape(self, s: str) -> str:
        # Replace ‣ by | to allow compatibility with latex menukeys extension
        # | is chosen because it is not escaped by Default LaTeX translator.
        return super().escape(s.replace(' ‣ ', '|'))

def setup(app):
    app.set_translator('latex', CustomLaTeXTranslator)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
