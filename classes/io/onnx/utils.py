import importlib
import onnx

import logging
logger = logging.getLogger(__name__)


def parse_mapping_from_path(mapping_path):
    """
    Parse the input accelerator residing in accelerator_path.
    """
    global module
    module = importlib.import_module(mapping_path)
    mapping = module.mapping
    if "default" in mapping:
        logger_str = ""
    else:
        logger_str = "not "
    logger.info(f"Parsed mapping with {len(mapping)} different entries. Default is {logger_str}present.")
    return mapping

def parse_onnx_model_from_path(onnx_model_path):
    return onnx.load(onnx_model_path, load_external_data=False)


def get_attribute_ints_with_name(name, attrs, default=None):
    """
    Retrieves the attrs[name_idx].ints from attrs.
    If it does not exist, the default provided by the caller is used.
    If the caller doesn't supply a default, an error is thrown.
    """
    attrs_names = [attr.name for attr in attrs]
    try:
        name_idx = attrs_names.index(name)
        return attrs[name_idx].ints
    except ValueError:
        if default is not None:
            return default
        else:
            raise ValueError(f"attrs has no attribute called {name}. Names = {attrs_names}.")


def get_node_input_output_dimension_shapes(node, model):
        value_info = model.graph.value_info
        if not value_info:
            raise ValueError("value_info of model is empty. Make sure you are loading in an inferred model. " \
            "See https://github.com/onnx/onnx/blob/main/docs/PythonAPIOverview.md#running-shape-inference-on-an-onnx-model")
        # get tensor names of the inputs and outputs of the model
        model_input_names = [input.name for input in model.graph.input]
        model_output_names = [output.name for output in model.graph.output]
        # get tensor names of the tensors in shapes
        shapes_names = [shape.name for shape in value_info]
        # get input and output activation dimension sizes
        # get input activation name
        ia_name = node.input[0]  # assumed it is the first input, don't see a way to otherwise know
        # check if this is a global input of the model, if so, retrieve dimension shape from model inputs
        if ia_name in model_input_names:
            # Find index of this input in list of input names
            ia_index = model_input_names.index(ia_name)
            ia_dimension_shape = [dim.dim_value for dim in model.graph.input[ia_index].type.tensor_type.shape.dim]
        else:  # it should be present in the shapes variable as it's not an input or output of the model
            ia_index = shapes_names.index(ia_name)
            ia_dimension_shape = [dim.dim_value for dim in value_info[ia_index].type.tensor_type.shape.dim]

        # repeat the same for the output activation of this layer
        oa_name = node.output[0]
        if oa_name in model_output_names:
            oa_index = model_output_names.index(oa_name)
            oa_dimension_shape = [dim.dim_value for dim in model.graph.output[oa_index].type.tensor_type.shape.dim]
        else:
            oa_index = shapes_names.index(oa_name)
            oa_dimension_shape = [dim.dim_value for dim in value_info[oa_index].type.tensor_type.shape.dim]

        return ia_dimension_shape, oa_dimension_shape