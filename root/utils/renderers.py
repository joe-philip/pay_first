from rest_framework.renderers import JSONRenderer as Renderer

from root.utils.base import success


class JSONRenderer(Renderer):
    """
    JSONRenderer is a custom renderer class that extends the default
    JSONRenderer to provide a standardized JSON response format.

    This renderer wraps the provided data using the `success`
    function before rendering, ensuring that all responses follow
    a consistent success structure.

    Methods:
        render(data, accepted_media_type=None, renderer_context=None):
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders the given data after wrapping it with a success response structure.

        Args:
            data (any): The data to be rendered.
            accepted_media_type (str, optional): The accepted media type for the response. Defaults to None.
            renderer_context (dict, optional): Additional context for rendering. Defaults to None.

        Returns:
            bytes: The rendered response data.
        """
        data = success(data)
        return super().render(data, accepted_media_type, renderer_context)
