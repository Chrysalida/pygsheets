import sys
from os import path
import pytest

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import pygsheets

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

CONFIG_FILENAME = path.join(path.dirname(__file__), 'data/tests.config')
CREDS_FILENAME = path.join(path.dirname(__file__), 'data/creds.json')


def read_config(filename):
    config = ConfigParser.ConfigParser()
    config.readfp(open(filename))
    return config

config = None
gc = None


def setup_module(module):
    global config, gc
    try:
        config = read_config(CONFIG_FILENAME)
    except IOError as e:
        msg = "Can't find %s for reading test configuration. "
        raise Exception(msg % e.filename)

    try:
        gc = pygsheets.authorize(CREDS_FILENAME)
    except IOError as e:
        msg = "Can't find %s for reading credentials. "
        raise Exception(msg % e.filename)

    config_title = config.get('Spreadsheet', 'title')
    sheets = [x for x in gc.list_ssheets() if x["name"] == config_title]
    for sheet in sheets:
        gc.delete(sheet['name'])


def teardown_module(module):
    config_title = config.get('Spreadsheet', 'title')
    sheets = [x for x in gc.list_ssheets() if x["name"] == config_title]
    for sheet in sheets:
        gc.delete(sheet['name'])


# @pytest.mark.skip()
class TestPyGsheets(object):

    @pytest.mark.order1
    def test_gc(self):
        assert(isinstance(gc, pygsheets.Client))

    @pytest.mark.order2
    def test_create(self):
        spreadsheet = gc.create(title=config.get('Spreadsheet', 'title'))
        assert(isinstance(spreadsheet, pygsheets.Spreadsheet))

    @pytest.mark.order3
    def test_delete(self):
        config_title = config.get('Spreadsheet', 'title')
        gc.delete(title=config_title)
        with pytest.raises(IndexError):
            dummy = [x for x in gc._spreadsheeets if x["name"] == config_title][0]


# @pytest.mark.skip()
class TestClient(object):
    def setup_class(self):
        title = config.get('Spreadsheet', 'title')
        self.spreadsheet = gc.create(title)

    def teardown_class(self):
        title = config.get('Spreadsheet', 'title')
        gc.delete(title=title)

    def test_open_title(self):
        title = config.get('Spreadsheet', 'title')
        spreadsheet = gc.open(title)
        assert(isinstance(spreadsheet, pygsheets.Spreadsheet))
        assert spreadsheet.title == spreadsheet.title

    def test_open_key(self):
        title = config.get('Spreadsheet', 'title')
        spreadsheet = gc.open_by_key(self.spreadsheet.id)
        assert(isinstance(spreadsheet, pygsheets.Spreadsheet))
        assert spreadsheet.id == self.spreadsheet.id
        assert spreadsheet.title == title

    def test_open_url(self):
        url = "https://docs.google.com/spreadsheets/d/"+self.spreadsheet.id
        spreadsheet = gc.open_by_url(url)
        assert(isinstance(spreadsheet, pygsheets.Spreadsheet))
        assert spreadsheet.id == self.spreadsheet.id


# @pytest.mark.skip()
class TestSpreadSheet(object):
    def setup_class(self):
        title = config.get('Spreadsheet', 'title')
        self.spreadsheet = gc.create(title)

    def teardown_class(self):
        title = config.get('Spreadsheet', 'title')
        gc.delete(title=title)

    def test_properties(self):
        json_sheet = self.spreadsheet._jsonsheet

        assert self.spreadsheet.id == json_sheet['spreadsheetId']
        assert self.spreadsheet.title == json_sheet['properties']['title']
        assert self.spreadsheet.defaultformat == json_sheet['properties']['defaultFormat']
        assert isinstance(self.spreadsheet.sheet1, pygsheets.Worksheet)

    def test_permissions(self):
        old_per = self.spreadsheet.list_permissions()
        assert isinstance(old_per, list)

        self.spreadsheet.share('comp.tech.nm@gmail.com')
        assert len(self.spreadsheet.list_permissions()) == (len(old_per)+1)

        self.spreadsheet.remove_permissions('comp.tech.nm@gmail.com')
        assert len(self.spreadsheet.list_permissions()) == len(old_per)

    def test_workssheet_add_del(self):
        self.spreadsheet.add_worksheet("testSheetx", 50, 60)
        try:
            wks = self.spreadsheet.worksheet_by_title("testSheetx")
        except pygsheets.WorksheetNotFound:
            pytest.fail()
        assert wks.rows == 50
        assert wks.cols == 60

        self.spreadsheet.del_worksheet(wks)
        with pytest.raises(pygsheets.WorksheetNotFound):
            self.spreadsheet.worksheet_by_title("testSheetx")

    def test_worksheet_opening(self):
        wkss = self.spreadsheet.worksheets()
        assert isinstance(wkss, list)
        assert isinstance(wkss[0], pygsheets.Worksheet)

        assert isinstance(self.spreadsheet.worksheet(), pygsheets.Worksheet)

    def add_worksheet(self):
        self.spreadsheet.add_worksheet("dummy_temp_wks", 100, 50)
        wks = self.spreadsheet.worksheet_by_title("dummy_temp_wks")
        assert isinstance(wks, pygsheets.Worksheet)
        assert wks.rows == 100
        assert wks.cols == 50

    def delete_worksheet(self):
        wks = self.spreadsheet.worksheet_by_title("dummy_temp_wks")
        self.spreadsheet.del_worksheet(wks)
        with pytest.raises(pygsheets.WorksheetNotFound):
            self.spreadsheet.worksheet_by_title("dummy_temp_wks")

    def test_share(self):
        self.spreadsheet.share("comp.tech.nm@gmail.com")
        plist = self.spreadsheet.list_permissions()
        permission = [x for x in plist if x['emailAddress'] == 'comp.tech.nm@gmail.com']
        assert len(permission) == 1
        assert isinstance(permission[0], dict)
        assert permission[0]['role'] == 'reader'

    def test_remove_permission(self):
        self.spreadsheet.remove_permissions("comp.tech.nm@gmail.com")
        plist = self.spreadsheet.list_permissions()
        permission = [x for x in plist if x['emailAddress'] == 'comp.tech.nm@gmail.com']
        assert len(permission) == 0
        assert not isinstance(permission, dict)


# @pytest.mark.skip()
class TestWorkSheet(object):
    def setup_class(self):
        title = config.get('Spreadsheet', 'title')
        self.spreadsheet = gc.create(title)
        self.worksheet = self.spreadsheet.worksheet()

    def teardown_class(self):
        title = config.get('Spreadsheet', 'title')
        gc.delete(title=title)

    def test_properties(self):
        json_sheet = self.worksheet.jsonSheet

        assert self.worksheet.id == json_sheet['properties']['sheetId']
        assert self.worksheet.title == json_sheet['properties']['title']
        assert self.worksheet.index == json_sheet['properties']['index']

    def test_resize(self):
        rows = self.worksheet.rows
        cols = self.worksheet.cols

        self.worksheet.cols = cols+1
        assert self.worksheet.cols == cols+1

        self.worksheet.add_cols(1)
        assert self.worksheet.cols == cols + 2

        self.worksheet.rows = rows + 1
        assert self.worksheet.rows == rows + 1

        self.worksheet.add_rows(1)
        assert self.worksheet.rows == rows + 2

        self.worksheet.resize(rows, cols)
        assert self.worksheet.cols == cols
        assert self.worksheet.rows == rows

    def test_addr_reformat(self):
        addr = pygsheets.Worksheet.get_addr((1, 1))
        assert addr == 'A1'

        addr = pygsheets.Worksheet.get_addr('A1')
        assert addr == (1, 1)

    def test_cell(self):
        assert isinstance(self.worksheet.cell('A1'), pygsheets.Cell)
        assert isinstance(self.worksheet.cell((1, 1)), pygsheets.Cell)

        with pytest.raises(pygsheets.CellNotFound):
            self.worksheet.cell((self.worksheet.rows + 5, self.worksheet.cols + 5))

    def test_insert_cols_rows(self):
        cols = self.worksheet.cols
        self.worksheet.insert_cols(1, 2)
        assert self.worksheet.cols == (cols+2)

        rows = self.worksheet.rows
        self.worksheet.insert_rows(1, 2)
        assert self.worksheet.rows == (rows + 2)

        with pytest.raises(pygsheets.InvalidArgumentValue):
            pygsheets.Worksheet.get_addr([1, 1])

    def test_values(self):
        self.worksheet.update_cell('A1', 'test val')
        vals = self.worksheet.values('A1', 'B4')
        assert isinstance(vals, list)
        assert vals[0][0] == 'test val'

        vals = self.worksheet.values('A1', (2, 2), 'cells')
        assert isinstance(vals, list)
        assert isinstance(vals[0][0], pygsheets.Cell)
        assert vals[0][0].value == 'test val'

    def test_update_cells(self):
        self.worksheet.update_cells(range='A1:B2', values=[[1, 2], [3, 4]])
        assert self.worksheet.cell((1, 1)).value == str(1)

        cells = [pygsheets.Cell('A1', 10), pygsheets.Cell('A2', 12)]
        cells = self.worksheet.update_cells(cell_list=cells)
        # assert self.worksheet.cell((1, 1)).value == cells[0].value

    def test_update_col(self):
        self.worksheet.update_col(5,[1,2,3,4,5])
        cols = self.worksheet.col(5)
        assert isinstance(cols, list)
        assert cols[3] == str(4)

    def test_update_row(self):
        self.worksheet.update_row(5,[1,2,3,4,5])
        rows = self.worksheet.row(5)
        assert isinstance(rows, list)
        assert rows[3] == str(4)

    def test_range(self):
        assert isinstance(self.worksheet.range('A1:A5'), list)

    def test_value_set(self):
        self.worksheet.update_cell('A1', 'xxx')
        assert self.worksheet.cell('A1').value == 'xxx'

    def test_iter(self):
        self.worksheet.update_row(1, [1, 2, 3, 4, 5])
        self.worksheet.update_row(2, [2, 3, 4, 5, 6])
        wks_iter = iter(self.worksheet)
        assert wks_iter.next() == [1, 2, 3, 4, 5]
        assert wks_iter.next() == [2, 3, 4, 5, 6]

    def test_getitem(self):
        self.worksheet.update_row(1, [1, 2, 3, 4, 5])
        row = self.worksheet[0]
        assert len(row) == self.worksheet.cols
        assert row[0][0] == str(1)

    def test_clear(self):
        self.worksheet.update_cell('S10', 100)
        self.worksheet.clear()
        assert self.worksheet.value


# @pytest.mark.skip()
class TestCell(object):
    def setup_class(self):
        title = config.get('Spreadsheet', 'title')
        self.spreadsheet = gc.create(title)
        self.worksheet = self.spreadsheet.worksheet()
        self.cell = self.worksheet.cell('A1')
        self.cell.value = 'test_value'

    def teardown_class(self):
        title = config.get('Spreadsheet', 'title')
        gc.delete(title=title)

    def test_properties(self):
        assert self.cell.row == 1
        assert self.cell.col == 1
        assert self.cell.value == 'test_value'
        assert self.cell.label == 'A1'

    def test_link(self):
        self.worksheet.update_cell('B2', 'new_val')
        self.cell.row = self.cell.row + 1
        self.cell.col = self.cell.col + 1

        assert self.cell.row == 2
        assert self.cell.col == 2
        assert self.cell.value == 'new_val'
        assert self.cell.label == 'B2'
