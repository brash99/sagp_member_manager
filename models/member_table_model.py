from PySide6.QtCore import Qt, QAbstractTableModel


def display(value):
    return "" if value is None else str(value)


class MemberTableModel(QAbstractTableModel):
    headers = [
        "First Name",
        "Last Name",
        "Institution",
        "Membership Status",
        "Primary Email",
        "Original Code",
    ]

    def __init__(self, members):
        super().__init__()
        self.members = members

    def set_members(self, members):
        self.beginResetModel()
        self.members = members
        self.endResetModel()

    def member_at(self, row):
        if 0 <= row < len(self.members):
            return self.members[row]
        return None

    def update_member(self, updated_member):
        for row, member in enumerate(self.members):
            if member.person_id == updated_member.person_id:
                self.members[row] = updated_member
                top_left = self.index(row, 0)
                bottom_right = self.index(row, self.columnCount() - 1)
                self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])
                return

    def rowCount(self, parent=None):
        return len(self.members)

    def columnCount(self, parent=None):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.headers[section]
        return str(section + 1)

    def data(self, index, role):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        member = self.members[index.row()]
        col = index.column()

        if col == 0:
            return display(member.first_name)
        if col == 1:
            return display(member.last_name)
        if col == 2:
            return display(member.institution)
        if col == 3:
            return display(member.membership_status)
        if col == 4:
            return display(member.primary_email)
        if col == 5:
            return display(member.original_membership_code)
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        key_functions = {
            0: lambda m: (m.first_name or '').lower(),
            1: lambda m: (m.last_name or '').lower(),
            2: lambda m: (m.institution or '').lower(),
            3: lambda m: (m.membership_status or '').lower(),
            4: lambda m: (m.primary_email or '').lower(),
            5: lambda m: (m.original_membership_code or '').lower(),
        }
        key_function = key_functions.get(column)
        if key_function is None:
            return
        self.layoutAboutToBeChanged.emit()
        self.members.sort(
            key=key_function,
            reverse=(order == Qt.DescendingOrder),
        )
        self.layoutChanged.emit()
