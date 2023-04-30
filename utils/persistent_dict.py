import struct
import pickle
import os
import tempfile

try:
    import aiofiles
    aiofiles_available = True
except ImportError:
    aiofiles_available = False


class PersistentDict(dict):
    def __init__(self, file_path, *args, **kwargs):
        """
        Initialize the PersistentDict object with the provided file path.
        Args:
            file_path (str): Path to the file where the data should be stored.
            *args, **kwargs: Arguments to be passed to the base class 'dict'.
        """
        super(PersistentDict, self).__init__(*args, **kwargs)
        self.file_path = file_path
        self._load_from_file()

    def _load_from_file(self):
        """
        Load data from the file specified in the file_path attribute and update the dictionary.
        This method is called automatically during initialization.
        """
        try:
            with open(self.file_path, 'rb') as file:
                while True:
                    length_length_data = file.read(4)
                    if not length_length_data:
                        break

                    length_length = int(struct.unpack("!I", length_length_data)[0])
                    length_data = file.read(length_length)
                    length = int(struct.unpack(f"!{length_length}s", length_data)[0])

                    serialized_data = file.read(length)
                    data_dict = pickle.loads(serialized_data)
                    super(PersistentDict, self).update(data_dict)
        except FileNotFoundError:
            pass

    def _append_to_file(self, data_dict, file_path):
        """
        Append the provided data dictionary to the file specified in the file_path attribute.
        Args:
            data_dict (dict): Dictionary containing the data to be appended to the file.
        """
        with open(file_path, 'ab') as file:
            serialized_data = pickle.dumps(data_dict)
            length = len(serialized_data)
            length_length = len(str(length))
            llv_format = struct.pack("!I", length_length) + struct.pack(f"!{length_length}s", str(length).encode()) + serialized_data
            file.write(llv_format)

    async def _append_to_file_async(self, data_dict, file_path):
        """
        Append the provided data dictionary to the file specified in the file_path attribute asynchronously.
        Args:
            data_dict (dict): Dictionary containing the data to be appended to the file.
        """
        async with aiofiles.open(file_path, 'ab') as file:
            serialized_data = pickle.dumps(data_dict)
            length = len(serialized_data)
            length_length = len(str(length))
            llv_format = struct.pack("!I", length_length) + struct.pack(f"!{length_length}s", str(length).encode()) + serialized_data
            await file.write(llv_format)

    def __setitem__(self, key, value):
        """
        Set a key-value pair in the dictionary and append the data to the file.
        Args:
            key: The key to be set in the dictionary.
            value: The value to be set for the key.
        """
        super(PersistentDict, self).__setitem__(key, value)
        self._append_to_file({key: value}, self.file_path)

    def update(self, data_dict):
        """
        Update the dictionary with the provided data dictionary and append the data to the file.
        Args:
            data_dict (dict): Dictionary containing the data to be updated in the dictionary.
        """
        super(PersistentDict, self).update(data_dict)
        self._append_to_file(data_dict, self.file_path)

    async def aset(self, key, value):
        """
        Set a key-value pair in the dictionary asynchronously and append the data to the file.
        Args:
            key: The key to be set in the dictionary.
            value: The value to be set for the key.
        """
        if not aiofiles_available:
            raise ImportError("aiofiles module not found. Please install it to use async methods.")
        super(PersistentDict, self).__setitem__(key, value)
        await self._append_to_file_async({key: value}, self.file_path)

    async def aupdate(self, data_dict):
        """
        Update the dictionary with the provided data dictionary asynchronously and append the data to the file.
        Args:
            data_dict (dict): Dictionary containing the data to be updated in the dictionary.
        """
        if not aiofiles_available:
            raise ImportError("aiofiles module not found. Please install it to use async methods.")
        super(PersistentDict, self).update(data_dict)
        await self._append_to_file_async(data_dict, self.file_path)

    def optimize_file(self):
        """
        Optimizes the file by removing the duplicates and sorting the keys.
        """
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            temp_file_path = temp_file.name
        original_dict = super(PersistentDict, self).copy()
        self._append_to_file(original_dict, temp_file_path)
        os.replace(temp_file_path, self.file_path)

    async def optimize_file_async(self):
        """
        Optimizes the file by removing the duplicates and sorting the keys.
        """
        async with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            temp_file_path = temp_file.name
        original_dict = super(PersistentDict, self).copy()
        await self._append_to_file_async(original_dict, temp_file_path)
        os.replace(temp_file_path, self.file_path)

    def __delitem__(self, key):
        raise NotImplementedError("Deletion of items is not supported in PersistentDict.")
