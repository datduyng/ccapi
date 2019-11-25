# imports - standard imports
from os.path import join, abspath
import re

# imports - module imports
from cc.core.querylist      import QueryList
from cc.core.mixins         import JupyterHTMLViewMixin
from cc.model.model.version import ModelVersion
from cc.util.system         import read
from cc.table               import Table
from cc.template            import render_template
from cc.constant            import MODEL_EXPORT_TYPE_MAP

# imports - boolean-model imports
from cc.model.resource                import Resource
from cc.model.model.boolean.component import (
    Component,
    InternalComponent, ExternalComponent
)
from cc.model.model.boolean.regulator    import (
    Regulator, PositiveRegulator, NegativeRegulator
)
from cc.model.model.boolean.condition    import (
    Condition,
    State    as ConditionState,
    Type     as ConditionType,
    Relation as ConditionRelation
)
from cc.model.model.boolean.subcondition import SubCondition

_ACCEPTED_COMPONENT_CLASSES = tuple([InternalComponent, ExternalComponent])

class BooleanModel(ModelVersion, JupyterHTMLViewMixin):
    """
    A Boolean Model.

    Usage::

        >>> from cc.model import Model, BooleanModel, InternalComponent
        >>> model    = Model('Cortical Area Development')
        >>> bool_    = BooleanModel()

        >>> Coup_fti = InternalComponent('Coup_fti')
        >>> Sp8      = InternalComponent('Sp8')
        >>> Pax6     = InternalComponent('Pax6')
        >>> Fgf8     = InternalComponent('Fgf8')
        >>> Emx2     = InternalComponent('Emx2')
        >>> bool_.add_components(Coup_fti, Sp8, Pax6, Fgf8, Emx2)
        
        >>> model.add_version(bool_)
        >>> model.save()
    """
    def __init__(self, *args, **kwargs):
        ModelVersion.__init__(self, *args, **kwargs)

        self._components = QueryList()

    @property
    def components(self):
        components = getattr(self, "_components", QueryList())
        return components

    @components.setter
    def components(self, value):
        if self.components == value:
            pass
        elif not isinstance(value, (list, tuple, QueryList)):
            raise TypeError("ID must be an integer.")
        else:
            self._components = value
        
        if not isinstance(value, QueryList):
            raise TypeError("Components must be of type (list, tuple, QueryList).")
        else:
            for component in value:
                if not isinstance(component, Component):
                    raise TypeError("Element must be of type Component, \
                        InternalComponent or ExternalComponent.")

            self._components = value

    @property
    def internal_components(self):
        # TODO: Use QueryList for query fetch.
        internal_components = [ ]

        for component in self.components:
            if isinstance(component, InternalComponent):
                internal_components.append(component)

        return internal_components

    @property
    def external_components(self):
        # TODO: Use QueryList for query fetch.
        external_components = [ ]

        for component in self.components:
            if isinstance(component, ExternalComponent):
                external_components.append(component)

        return external_components

    def add_component(self, component):
        if not isinstance(component, _ACCEPTED_COMPONENT_CLASSES):
            raise TypeError("Component must be of type %s, found %s." % 
                (_ACCEPTED_COMPONENT_CLASSES, type(component))
            )
        else:
            if component in self.components:
                raise ValueError("Component already exists.")
            else:
                self.components.append(component)

    def add_components(self, *components):
        for component in components:
            if not isinstance(component, _ACCEPTED_COMPONENT_CLASSES):
                raise TypeError("Component must be of type %s, found %s." % 
                    (_ACCEPTED_COMPONENT_CLASSES, type(component))
                )

        for component in components:
            self.add_component(component)

    def _repr_html_(self):
        repr_ = render_template(join("boolean", "model.html"), context = dict({
            "id":                   self.id,
            "version":              self.version,
            "name":                 self.name,
            "memory_address":       "0x0%x" % id(self),
            "number_of_components": len(self.components),
            "components":           ", ".join([s.name for s in self.components])
        }))
        return repr_

    def draw(self, type_ = "networkx", **kwargs):
        if type_ == "networkx":
            try:
                import networkx as nx
            except ImportError:
                raise ImportError("Unable to draw using networkx. Please install networkx \
                    https://networkx.github.io/documentation/stable/install.html")
                    
            try:
                from   networkx.drawing.nx_agraph import graphviz_layout
            except ImportError:
                raise ImportError("Unable to use graphviz_layout. Please install pygraphviz \
                    https://pygraphviz.github.io/")
            
            graph  = nx.DiGraph()
            graph.add_nodes_from([c.name for c in self.components])

            layout = graphviz_layout(graph)

            nx.draw_networkx_nodes(graph, layout,
                nodelist    = [c.name for c in self.internal_components],
                node_color  = 'b',
                alpha       = 0.8
            )
            nx.draw_networkx_nodes(graph, layout,
                nodelist    = [c.name for c in self.external_components],
                node_color  = 'r',
                alpha       = 0.8
            )

            def get_edges(type_):
                edges      = [ ]

                for component in self.internal_components:
                    for regulator in component.regulators:
                        if regulator.type == type_:
                            edges.append([
                                component.name,
                                regulator.component.name
                            ])
                
                return edges

            edges = get_edges("positive")
            nx.draw_networkx_edges(graph, layout,
                edgelist    = edges,
                alpha       = 0.5,
                edge_color  = 'g'
            )

            edges = get_edges("negative")
            nx.draw_networkx_edges(graph, layout,
                edgelist    = edges,
                alpha       = 0.5,
                edge_color  = 'r'
            )

            labels = dict((c.name, c.name) for c in self.components)
            nx.draw_networkx_labels(graph, layout, labels)
        elif type_ == "cytoscape":
            pass
        else:
            raise TypeError("No drawing type %s found." % type_)

    def summary(self):
        table    = Table(header = ["Internal Components (+, -)", "External Components"])

        internal = self.internal_components
        external = self.external_components

        maximum  = max(len(internal), len(external))

        for _ in range(maximum):
            row = [ ]

            if len(internal):
                component   = internal.pop(0)
                value       = "%s (%s,%s)" % (
                    component.name,
                    len(component.positive_regulators),
                    len(component.negative_regulators)
                )
                row.append(value)

            if len(external):
                component = external.pop(0)
                row.append(component.name)

            table.insert(row)

        string = table.render()

        print(string)

    # def export(self, path = None, type_ = "sbml", **kwargs):
    #     url             = self._client._build_url("_api", "model", "export", self.id)
    #     type_           = MODEL_EXPORT_TYPE_MAP[type_]
    #     params          = { "version": self.version, "type": type_ }

    #     response        = self._client._request("GET", url, params = params)

    #     default_path    = False

    #     if not path:
    #         default_path = True

    #         header  = response.headers["content-disposition"]
    #         name    = re.findall("filename=(.+)", header)[0]

    #         path    = abspath(name)

    #     nchunk      = kwargs.get("nchunk", 1024)

    #     with open(path, "wb") as f:
    #         for chunk in response.iter_content(chunk_size = nchunk):
    #             if chunk:
    #                 f.write(chunk)

    #     if default_path:
    #         return path