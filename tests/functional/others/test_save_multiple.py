import os

import pytest
from nbformat.v4.nbbase import new_notebook
from nbformat.validator import NotebookValidationError
from tornado.web import HTTPError

import jupytext
from jupytext.compare import compare_notebooks, notebook_model
from jupytext.contentsmanager import TextFileContentsManager


async def test_rmd_is_ok(ipynb_file, cm, tmpdir):
    nb = jupytext.read(ipynb_file)
    tmp_ipynb = "notebook.ipynb"
    tmp_rmd = "notebook.Rmd"

    nb.metadata.setdefault("jupytext", {})["formats"] = "ipynb,Rmd"

    cm = TextFileContentsManager()
    cm.root_dir = str(tmpdir)

    await cm.save(model=notebook_model(nb), path=tmp_ipynb)

    nb2 = jupytext.read(str(tmpdir.join(tmp_rmd)))

    compare_notebooks(nb2, nb, "Rmd")


async def test_ipynb_is_ok(rmd_file, cm, tmpdir):
    nb = jupytext.read(rmd_file)
    tmp_ipynb = "notebook.ipynb"
    tmp_rmd = "notebook.Rmd"

    cm.root_dir = str(tmpdir)
    cm.formats = "ipynb,Rmd"

    await cm.save(model=notebook_model(nb), path=tmp_rmd)

    nb2 = jupytext.read(str(tmpdir.join(tmp_ipynb)))
    compare_notebooks(nb2, nb)


async def test_all_files_created(ipynb_py_file, tmpdir):
    nb = jupytext.read(ipynb_py_file)
    tmp_ipynb = "notebook.ipynb"
    tmp_rmd = "notebook.Rmd"
    tmp_py = "notebook.py"
    nb.metadata["jupytext"] = {"formats": "ipynb,Rmd,py"}

    cm = TextFileContentsManager()
    cm.root_dir = str(tmpdir)

    await cm.save(model=notebook_model(nb), path=tmp_ipynb)

    nb2 = jupytext.read(str(tmpdir.join(tmp_py)))
    compare_notebooks(nb2, nb)

    nb3 = jupytext.read(str(tmpdir.join(tmp_rmd)))
    compare_notebooks(nb3, nb, "Rmd")


async def test_no_files_created_on_no_format(tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_rmd = "notebook.Rmd"
    tmp_py = "notebook.py"

    cm = TextFileContentsManager()
    cm.root_dir = str(tmpdir)
    cm.formats = ""

    await cm.save(
        model=notebook_model(new_notebook(nbformat=4, metadata=dict())),
        path=tmp_ipynb,
    )

    assert not os.path.isfile(str(tmpdir.join(tmp_py)))
    assert not os.path.isfile(str(tmpdir.join(tmp_rmd)))


async def test_raise_on_wrong_format(tmpdir):
    tmp_ipynb = str(tmpdir.join("notebook.ipynb"))

    cm = TextFileContentsManager()
    cm.root_dir = str(tmpdir)

    with pytest.raises(HTTPError):
        await cm.save(
            path=tmp_ipynb,
            model=dict(
                type="notebook",
                content=new_notebook(
                    nbformat=4, metadata=dict(jupytext_formats=[".doc"])
                ),
            ),
        )


async def test_no_rmd_on_not_notebook(tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_rmd = "notebook.Rmd"

    cm = TextFileContentsManager()
    cm.root_dir = str(tmpdir)
    cm.formats = "ipynb,Rmd"

    with pytest.raises(HTTPError):
        await cm.save(
            model=dict(type="not notebook", content=new_notebook()), path=tmp_ipynb
        )
    assert not os.path.isfile(str(tmpdir.join(tmp_rmd)))


async def test_no_rmd_on_not_v4(tmpdir):
    tmp_ipynb = "notebook.ipynb"
    tmp_rmd = "notebook.Rmd"

    cm = TextFileContentsManager()
    cm.root_dir = str(tmpdir)
    cm.formats = "ipynb,Rmd"

    with pytest.raises(NotebookValidationError):
        await cm.save(model=notebook_model(new_notebook(nbformat=3)), path=tmp_rmd)

    assert not os.path.isfile(str(tmpdir.join(tmp_ipynb)))
