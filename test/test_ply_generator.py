
import string
import tempfile

from hypothesis import given, strategies as st
from hypothesis.extra.numpy import arrays

import os, sys; sys.path.insert(0, os.path.abspath('.')); del sys; del os
import plyfile

# A useful subset of all valid identifiers (no numbers as they may not lead)
st_valid_names = st.text(min_size=1, alphabet=string.ascii_letters + '_')


@st.composite
def st_ascii_comments(draw):
    """Most unicode strings are not valid comments in a .ply file.
    Comments must be ASCII, may not contain leading or trailing whitespace,
    and may not contain "\r\n".
    """
    # TODO: plyfile object constructors should enforce these properties
    return [s.strip().replace('\r\n', '') for s in
            draw(st.lists(elements=st.characters(max_codepoint=127)))]


@st.composite
def st_structured_arrays(draw, min_size=1, max_size=20):
    """Create arrays that can be described as a valid PlyElement"""
    st_dtypes = st.lists(elements=st.tuples(
        st_valid_names, st.sampled_from(set(plyfile._data_type_reverse))),
                         min_size=1, unique_by=lambda d: d[0])
    return draw(arrays(
        draw(st_dtypes),
        draw(st.integers(min_value=min_size, max_value=max_size)),
        elements=st.binary()))


# Strategy to generate arbitary PlyElement instances
st_PlyElement = st.builds(
    target=plyfile.PlyElement.describe,
    data=st_structured_arrays(),
    name=st_valid_names,
    comments=st_ascii_comments()
    )


# Strategy to generate arbitary PlyData instances
st_PlyData = st.builds(
    target=plyfile.PlyData,
    elements=st.lists(elements=st_PlyElement, unique_by=lambda e: e.name),
    text=st.booleans(),
    byte_order=st.sampled_from(plyfile._byte_order_map.values()),
    comments=st_ascii_comments(),
    obj_info=st_ascii_comments()
    )


@given(st_PlyData)
def test_write_read_write(plydata):
    with tempfile.TemporaryFile() as f1, tempfile.TemporaryFile() as f2:
        plydata.write(f1)
        f1.seek(0)
        plyfile.PlyData.read(f1).write(f2)
        f1.seek(0)
        f2.seek(0)
        assert f1.read() == f2.read()

