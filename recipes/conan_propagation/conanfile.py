from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import get, copy, save, export_conandata_patches
import os
import textwrap


class PropagateConan(ConanFile):
    name = "propagate"
    license = "MIT"
    url = "https://github.com/fajkoson/propagation"
    description = "Minimal propagation test library with tool and shared lib"
    topics = ("test", "propagation", "tool_requires")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"

    options = {
        "shared": [True, False],
        "build_executable": [True, False],
    }
    default_options = {
        "shared": True,
        "build_executable": True,
    }

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # But it won’t make this variable available in the consumer's CMakeLists.txt, it works only in current project
        tc = CMakeToolchain(self)
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["PROPAGATE_BUILD_EXECUTABLE"] = self.options.build_executable
        tc.variables["CMAKE_INSTALL_BINDIR"] = "bin"
        tc.variables["CMAKE_INSTALL_LIBDIR"] = "lib"
        tc.variables["CMAKE_INSTALL_INCLUDEDIR"] = "include"
        tc.generate()


    def build_id(self):
        del self.info_build.settings.compiler
        del self.info_build.settings.build_type

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        build_type_folder = os.path.join(self.build_folder, str(self.settings.build_type))

        include_dir = os.path.join(self.package_folder, "include")
        lib_dir = os.path.join(self.package_folder, "lib")
        bin_dir = os.path.join(self.package_folder, "bin")
        cmake_dir = os.path.join(self.package_folder, "lib", "cmake", self.name)

        os.makedirs(include_dir, exist_ok=True)
        os.makedirs(lib_dir, exist_ok=True)
        os.makedirs(bin_dir, exist_ok=True)
        os.makedirs(cmake_dir, exist_ok=True)

        copy(self, "propagate.h", dst=include_dir, src=os.path.join(self.source_folder, "include"))
        copy(self, "*.lib", dst=lib_dir, src=build_type_folder, keep_path=False)
        copy(self, "*.dll", dst=bin_dir, src=build_type_folder, keep_path=False)
        copy(self, "*.pdb", dst=bin_dir, src=build_type_folder, keep_path=False)

        if self.options.build_executable:
            copy(self, "propagate_exec.exe", dst=bin_dir, src=build_type_folder, keep_path=False)

        self._create_cmake_module_variables(os.path.join(cmake_dir, "propagate.cmake"))


    def _create_cmake_module_variables(self, module_file):
        content = textwrap.dedent(
            f"""\
            set(PROPAGATE_FOUND TRUE)
            set(PROPAGATE_EXECUTABLE "${{CMAKE_CURRENT_LIST_DIR}}/../../../bin/propagate_exec.exe")
            set(PROPAGATE_VERSION "{self.version}")
        """
        )
        save(self, module_file, content)

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", self.name, "propagate.cmake")

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_target_name", "propagate::propagate")
        self.cpp_info.set_property("cmake_file_name", "propagate")
        self.cpp_info.set_property("cmake_build_modules", [self._module_file_rel_path])

        self.cpp_info.libs = ["propagate"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.bindirs = ["bin"]

        self.runenv_info.append_path("PATH", os.path.join(self.package_folder, "bin"))
