# Common settings for MSVC
function(set_common_msvc_options TARGET_NAME)

  target_compile_options(${TARGET_NAME} PRIVATE "-W4") # Sets warning level.

  # FIXME: Visual studio does not deactivate warnings so for now warnings do not
  # result in errors. target_compile_options(${TARGET_NAME} PRIVATE "-WX")

  # target_compile_options( ${TARGET_NAME} PRIVATE "-wd4127") # conditional
  # expression is constant

  # target_compile_options( ${TARGET_NAME} PRIVATE "-wd4244") # 'conversion'
  # conversion from 'type1' to 'type2', possible loss of data

  target_compile_options(${TARGET_NAME} PRIVATE "-permissive-")
  target_compile_options(${TARGET_NAME} PRIVATE "-EHsc")
  target_compile_options(${TARGET_NAME} PRIVATE "-bigobj")

  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Debug>:-D_DEBUG>)
  if(BUILD_SHARED_LIBS)
    target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Debug>:-MDd>)
  else() 
    target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Debug>:-MTd>)
  endif(NOT BUILD_SHARED_LIBS)

  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Debug>:-Ob0>
  )# Disables inline expansion
  target_compile_options(
    ${TARGET_NAME} PRIVATE $<$<CONFIG:Debug>:-Od>) # Disables optimization,
                                                   # speeding compilation and
                                                   # simplifying debugging. http
                                                   # s://msdn.microsoft.com/en-
                                                   # us/library/k1ack8f1.aspx
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Debug>:-RTC1>
  )# Enables run-time error checking.
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Debug>:-Zi>
  )# Generates complete debugging information.

  target_compile_options(${TARGET_NAME}
                         PRIVATE $<$<CONFIG:RelWithDebInfo>:-D_NDEBUG>)
  target_compile_options(${TARGET_NAME}
                         PRIVATE $<$<CONFIG:RelWithDebInfo>:-DNDEBUG>)
  if(BUILD_SHARED_LIBS)                         
    target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:RelWithDebInfo>:-MD>)
  else() 
    target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:RelWithDebInfo>:-MT>)
  endif(NOT BUILD_SHARED_LIBS)

  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:RelWithDebInfo>:-O2>
  )# Creates fast code.
  target_compile_options(
    ${TARGET_NAME} PRIVATE $<$<CONFIG:RelWithDebInfo>:-Ob2>) # The default
                                                             # value. Allows
                                                             # expansion of
                                                             # functions marked
                                                             # as inline,
                                                             # __inline, or
                                                             # __forceinline,
                                                             # and any other
                                                             # function that the
                                                             # compiler chooses.
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:RelWithDebInfo>:-Oi>
  )# Generates intrinsic functions.
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:RelWithDebInfo>:-Ot>
  )# Favors fast code.
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:RelWithDebInfo>:-Zi>
  )# Generates complete debugging information.

  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-D_NDEBUG>)
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-DNDEBUG>)

  if(BUILD_SHARED_LIBS)
    target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-MD>)
  else()
    target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-MT>)
  endif(NOT BUILD_SHARED_LIBS)

  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-O2>
  )# Creates fast code.
  target_compile_options(
    ${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-Ob2>) # The default value.
                                                      # Allows expansion of
                                                      # functions marked as
                                                      # inline, __inline, or
                                                      # __forceinline, and any
                                                      # other function that the
                                                      # compiler chooses.
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-Oi>
  )# Generates intrinsic functions.
  target_compile_options(${TARGET_NAME} PRIVATE $<$<CONFIG:Release>:-Ot>
  )# Favors fast code.

endfunction()

# Disabled warnings for souffle projects on MSVC
function(set_souffle_msvc_options TARGET_NAME)
  target_compile_definitions(${TARGET_NAME} PRIVATE _CRT_SECURE_NO_WARNINGS)
  target_compile_definitions(${TARGET_NAME} PRIVATE _CRT_NONSTDC_NO_WARNINGS)

  # From cpp generated by souffle:
  target_compile_options(
    ${TARGET_NAME} PRIVATE -wd4146) # unary minus operator applied to unsigned
                                    # type, result still unsigned
  target_compile_options(
    ${TARGET_NAME} PRIVATE -wd4189) # 'identifier' : local variable is
                                    # initialized but not referenced

  # From souffle headers
  target_compile_options(
    ${TARGET_NAME} PRIVATE -wd4267) # conversion from 'type1' to 'type2',
                                    # possible loss of data

  target_compile_options(
    ${TARGET_NAME} PRIVATE -wd4456) # declaration of 'decl' hides previous local
                                    # declaration
endfunction()

# ===== generated souffle code =====
find_program(
  SOUFFLE souffle
  HINTS $ENV{PATH}
  DOC "souffle must be in your PATH to build disassembler.")
if(NOT SOUFFLE)
  message(FATAL_ERROR "souffle was not found in your PATH. Unable to build.")
endif()
if(NOT SOUFFLE_INCLUDE_DIR)
  get_filename_component(SOUFFLE_BIN_DIR ${SOUFFLE} DIRECTORY)
  get_filename_component(SOUFFLE_INCLUDE_DIR ${SOUFFLE_BIN_DIR}/../include
                         ABSOLUTE)
  if(NOT EXISTS ${SOUFFLE_INCLUDE_DIR}/souffle)
    message(WARNING "SOUFFLE_INCLUDE_DIR not found")
    unset(SOUFFLE_INCLUDE_DIR)
  endif()
  unset(SOUFFLE_BIN_DIR)
endif()

# Souffle searches for a "mcpp" binary, even on Windows, where "mcpp.exe" would
# probably make more sense. We explicitly provide the preprocessor.
if(WIN32)
  set(SOUFFLE_PREPROCESSOR_ARG "--preprocessor=mcpp.exe")
else()
  set(SOUFFLE_PREPROCESSOR_ARG "")
endif()

if(DDISASM_SOUFFLE_PROFILING)
  # We only need the presence of the argument.
  set(SOUFFLE_PROFILING_ARG "--profile=")
else()
  set(SOUFFLE_PROFILING_ARG "")
endif()

set(DATALOG_BASE_SOURCES
    datalog/arch/arch.dl
    datalog/binary/elf/elf_binaries.dl
    datalog/binary/elf/exceptions.dl
    datalog/binary/elf/relocations.dl
    datalog/binary/elf/symbolization.dl
    datalog/binary/elf/tls.dl
    datalog/binary/pe/pe_binaries.dl
    datalog/binary/pe/exceptions.dl
    datalog/binary/pe/relocations.dl
    datalog/basic_def_used.dl
    datalog/bitmasks.dl
    datalog/boundary_value_analysis.dl
    datalog/code_inference.dl
    datalog/code_inference_postprocess.dl
    datalog/cfg.dl
    datalog/data.dl
    datalog/data_access_analysis.dl
    datalog/empty_range.dl
    datalog/basic_function_inference.dl
    datalog/jump_tables.dl
    datalog/main.dl
    datalog/noreturn.dl
    datalog/pointer_reattribution.dl
    datalog/register_type_analysis.dl
    datalog/relative_jump_tables.dl
    datalog/symbols.dl
    datalog/symbolization.dl
    datalog/use_def_analysis.dl
    datalog/value_analysis.dl
    datalog/debug_stats.dl
    datalog/self_diagnose.dl
    datalog/straight_line_def_used.dl)

set(SOUFFLE_DATALOG_DIR ${CMAKE_CURRENT_SOURCE_DIR}/datalog/)

function(GENERATE_ARCH_CPP_SINGLE)
  cmake_parse_arguments(PARAM "" "ARCH;MARCH;PATH" "DATALOG_SOURCES" ${ARGV})

  string(TOLOWER ${PARAM_ARCH} ARCH)
  add_custom_command(
    OUTPUT "${PARAM_PATH}.cpp"
    WORKING_DIRECTORY "${SOUFFLE_DATALOG_DIR}"
    COMMAND
      ${SOUFFLE} main.dl -g "${CMAKE_BINARY_DIR}/src/${PARAM_PATH}.cpp" -jauto
      -MARCH_${PARAM_MARCH} ${SOUFFLE_PREPROCESSOR_ARG} ${SOUFFLE_PROFILING_ARG}
      -N ddisasm_${ARCH}
    DEPENDS ${DATALOG_BASE_SOURCES} ${PARAM_DATALOG_SOURCES})
endfunction()

function(GENERATE_ARCH_CPP_MANY)
  cmake_parse_arguments(PARAM "" "ARCH;MARCH;PATH" "DATALOG_SOURCES" ${ARGV})
  string(TOLOWER ${PARAM_ARCH} ARCH)
  set(STAGING_PATH ${CMAKE_BINARY_DIR}/src/souffle_disasm_${ARCH}.staging/)

  # Force reconfiguration if any of the datalog sources changed.
  get_directory_property(OLD_DEPS CMAKE_CONFIGURE_DEPENDS)
  set(NEW_DEPS "${OLD_DEPS};${DATALOG_BASE_SOURCES};${PARAM_DATALOG_SOURCES}")
  list(REMOVE_DUPLICATES NEW_DEPS)
  set_directory_properties(PROPERTIES CMAKE_CONFIGURE_DEPENDS "${NEW_DEPS}")

  # Recreate the staging directory
  file(REMOVE_RECURSE ${STAGING_PATH})
  file(MAKE_DIRECTORY ${STAGING_PATH})
  file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/src/${PARAM_PATH})

  # Generate CPP code
  execute_process(
    COMMAND
      ${SOUFFLE} main.dl -G ${STAGING_PATH} -jauto -MARCH_${PARAM_MARCH}
      ${SOUFFLE_PREPROCESSOR_ARG} ${SOUFFLE_PROFILING_ARG} -N ddisasm_${ARCH}
    WORKING_DIRECTORY "${SOUFFLE_DATALOG_DIR}")

  # Remove stale files from final generator output directory
  file(
    GLOB GENERATED_FILES
    RELATIVE "${CMAKE_BINARY_DIR}/src/${PARAM_PATH}/"
    "${CMAKE_BINARY_DIR}/src/${PARAM_PATH}/*")
  foreach(FILE ${GENERATED_FILES})
    if(NOT EXISTS "${STAGING_PATH}/${FILE}")
      file(REMOVE "${CMAKE_BINARY_DIR}/src/${PARAM_PATH}/${FILE}")
    endif()
  endforeach()

  # Copy modified files from staging to final generator output directory
  file(
    GLOB GENERATED_FILES
    RELATIVE "${STAGING_PATH}/"
    "${STAGING_PATH}/*")
  foreach(FILE ${GENERATED_FILES})
    execute_process(
      COMMAND ${CMAKE_COMMAND} -E copy_if_different "${STAGING_PATH}/${FILE}"
              "${CMAKE_BINARY_DIR}/src/${PARAM_PATH}")
  endforeach()
endfunction()

function(GENERATE_ARCH_STATIC_LIB)
  cmake_parse_arguments(PARAM "" "ARCH;MARCH;PATH" "DATALOG_SOURCES" ${ARGV})

  string(TOLOWER ${PARAM_ARCH} ARCH)
  set(GENERATED_CPP_PATH ${CMAKE_BINARY_DIR}/src/${PARAM_PATH})

  if(DDISASM_GENERATE_MANY)
    generate_arch_cpp_many(${ARGV})
  else()
    generate_arch_cpp_single(${ARGV})
  endif()

  if(DDISASM_GENERATE_MANY)
    file(GLOB GENERATED_CPP CONFIGURE_DEPENDS "${GENERATED_CPP_PATH}/*")
  else()
    set(GENERATED_CPP "${GENERATED_CPP_PATH}.cpp")
  endif()

  # Build generated code as a static library. Each arch needs its own library to
  # build with unique include paths. It also different compilation flags than
  # the rest of the source (because the generated souffle code won't build with
  # -Wall -Werror).
  add_library(ddisasm_datalog_${ARCH} STATIC ${GENERATED_CPP})

  target_compile_definitions(ddisasm_datalog_${ARCH} PRIVATE
                             __EMBEDDED_SOUFFLE__)
  target_compile_definitions(ddisasm_datalog_${ARCH} PRIVATE RAM_DOMAIN_SIZE=64)
  target_compile_options(ddisasm_datalog_${ARCH} PRIVATE ${OPENMP_FLAGS})

  target_include_directories(ddisasm_datalog_${ARCH}
                             PRIVATE ${GENERATED_CPP_PATH})
  if(SOUFFLE_INCLUDE_DIR)
    target_include_directories(ddisasm_datalog_${ARCH} SYSTEM
                               PRIVATE ${SOUFFLE_INCLUDE_DIR})
  endif()

  if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
    target_link_options(ddisasm_datalog_${ARCH} PRIVATE -NODEFAULTLIB:LIBCMTD)

    set_common_msvc_options(ddisasm_datalog_${ARCH})
    set_souffle_msvc_options(ddisasm_datalog_${ARCH})
  else()
    target_compile_options(ddisasm_datalog_${ARCH} PRIVATE -O3)
    target_compile_options(
      ddisasm_datalog_${ARCH} PRIVATE -Wno-parentheses-equality
                                      -Wno-unused-parameter)
  endif()

  # Disable var-tracking-assignments - uses too much memory when building
  # datalog code.
  if(${CMAKE_CXX_COMPILER_ID} STREQUAL GNU)
    target_compile_options(ddisasm_datalog_${ARCH}
                           PRIVATE -fno-var-tracking-assignments)
  endif()

  list(APPEND GENERATED_STATIC_LIB ddisasm_datalog_${ARCH})
  set(GENERATED_STATIC_LIB
      ${GENERATED_STATIC_LIB}
      PARENT_SCOPE)
endfunction()

# determine what flags to use to specify -fopenmp.
if(${CMAKE_CXX_COMPILER_ID} STREQUAL GNU)
  set(OPENMP_FLAGS -fopenmp)
elseif(${CMAKE_CXX_COMPILER_ID} STREQUAL Clang)
  set(OPENMP_FLAGS -fopenmp=libgomp)
endif()

if(DDISASM_ARM_32)
  add_definitions(-DDDISASM_ARM_32)

  set(DATALOG_ARM32_SOURCES
      datalog/arch/arm32/arch_arm.dl
      datalog/arch/arm32/float_operations.dl
      datalog/arch/arm32/jump_operations.dl
      datalog/arch/arm32/registers.dl
      datalog/arch/arm32/memory_access.dl
      datalog/arch/arm_binaries.dl
      datalog/arch/arm32_binaries.dl
      datalog/arch/arm32_code_inference.dl
      datalog/arch/arm32_jump_tables.dl
      datalog/arch/arm32_symbolization.dl)

  generate_arch_static_lib(
    ARCH
    ARM32
    MARCH
    ARM32
    DATALOG_SOURCES
    ${DATALOG_ARM32_SOURCES}
    PATH
    souffle_disasm_arm32)
endif()

if(DDISASM_ARM_64)
  add_definitions(-DDDISASM_ARM_64)

  set(DATALOG_ARM64_SOURCES
      datalog/arch/arm64/arch_arm64.dl
      datalog/arch/arm64/float_operations.dl
      datalog/arch/arm64/jump_operations.dl
      datalog/arch/arm64/registers.dl
      datalog/arch/arm64/memory_access.dl
      datalog/arch/arm_binaries.dl
      datalog/arch/arm64_symbolization.dl)

  generate_arch_static_lib(
    ARCH
    ARM64
    MARCH
    ARM64
    DATALOG_SOURCES
    ${DATALOG_ARM64_SOURCES}
    PATH
    souffle_disasm_arm64)
endif()

if(DDISASM_MIPS_32)
  add_definitions(-DDDISASM_MIPS_32)

  set(DATALOG_MIPS32_SOURCES
      datalog/arch/mips32/arch_mips32.dl
      datalog/arch/mips32/float_operations.dl
      datalog/arch/mips32/jump_operations.dl
      datalog/arch/mips32/memory_access.dl
      datalog/arch/mips32/registers.dl
      datalog/arch/mips_symbolization.dl)

  generate_arch_static_lib(
    ARCH
    MIPS32
    MARCH
    MIPS32
    DATALOG_SOURCES
    ${DATALOG_MIPS32_SOURCES}
    PATH
    souffle_disasm_mips32)
endif()

if(DDISASM_X86_32)
  add_definitions(-DDDISASM_X86_32)

  set(DATALOG_X86_32_SOURCES
      datalog/arch/intel/arch_x86_32.dl
      datalog/arch/intel/float_operations.dl
      datalog/arch/intel/jump_operations.dl
      datalog/arch/intel/registers_common.dl
      datalog/arch/intel/registers_x86_32.dl
      datalog/arch/intel/arch_x86.dl
      datalog/arch/intel/memory_access.dl
      datalog/arch/x86_32_symbolization.dl)

  generate_arch_static_lib(
    ARCH
    x86_32
    MARCH
    IA32
    DATALOG_SOURCES
    ${DATALOG_X86_32_SOURCES}
    PATH
    souffle_disasm_x86_32)
endif()

if(DDISASM_X86_64)
  add_definitions(-DDDISASM_X86_64)

  set(DATALOG_X86_64_SOURCES
      datalog/arch/intel/arch_x86_64.dl
      datalog/arch/intel/float_operations.dl
      datalog/arch/intel/jump_operations.dl
      datalog/arch/intel/registers_common.dl
      datalog/arch/intel/registers_x86_64.dl
      datalog/arch/intel/arch_x86.dl
      datalog/arch/intel/memory_access.dl
      datalog/arch/x86_64_symbolization.dl)

  generate_arch_static_lib(
    ARCH
    x86_64
    MARCH
    AMD64
    DATALOG_SOURCES
    ${DATALOG_X86_64_SOURCES}
    PATH
    souffle_disasm_x86_64)
endif()

# ====== builder ===========

add_subdirectory(gtirb-builder)

# ====== decoder ===========

add_subdirectory(gtirb-decoder)

# ====== passes ============

add_subdirectory(passes)

# ===== functors ====
# Build a shared functors library for use with the interpreter. Disabled if
# BUILD_SHARED_LIBS is OFF
if(BUILD_SHARED_LIBS)
  add_library(functors SHARED Functors.cpp)
  target_link_libraries(functors gtirb)

  target_compile_definitions(functors PRIVATE -DSOUFFLE_INTERPRETER_FUNCTOR_LIB)

  if(${CMAKE_CXX_COMPILER_ID} STREQUAL GNU)
    target_compile_options(functors PRIVATE -Wno-unused-parameter)
  endif()

  target_include_directories(
    functors PRIVATE $<BUILD_INTERFACE:${CMAKE_BINARY_DIR}/include>)

  target_compile_options(functors PRIVATE ${OPENMP_FLAGS})
  target_compile_definitions(functors PRIVATE RAM_DOMAIN_SIZE=64)
  if(SOUFFLE_INCLUDE_DIR)
    target_include_directories(functors SYSTEM PRIVATE ${SOUFFLE_INCLUDE_DIR})
  endif()

  if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
    target_compile_definitions(functors PRIVATE _CRT_SECURE_NO_WARNINGS)
    target_compile_definitions(functors PRIVATE _CRT_NONSTDC_NO_WARNINGS)
    set_common_msvc_options(functors)
  else()
    target_compile_options(functors PRIVATE -O3)
    target_compile_options(functors PRIVATE -Wall)
    target_compile_options(functors PRIVATE -Wextra -Wpointer-arith)
    target_compile_options(functors PRIVATE -Werror)
  endif()
endif()

# ====== ddisasm_pipeline ===========
add_library(ddisasm_pipeline STATIC CliDriver.cpp Hints.cpp
                                    AnalysisPipeline.cpp)

if(SOUFFLE_INCLUDE_DIR)
  target_include_directories(ddisasm_pipeline SYSTEM
                             PRIVATE ${SOUFFLE_INCLUDE_DIR})
endif()

target_compile_definitions(ddisasm_pipeline PRIVATE __EMBEDDED_SOUFFLE__)
target_compile_definitions(ddisasm_pipeline PRIVATE RAM_DOMAIN_SIZE=64)
target_compile_options(ddisasm_pipeline PRIVATE ${OPENMP_FLAGS})

if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
  set_common_msvc_options(ddisasm_pipeline)
endif()

target_link_libraries(ddisasm_pipeline PRIVATE gtirb gtirb_decoder)

# ====== ddisasm ===========
# Build final ddisasm executable
add_executable(ddisasm Registration.cpp Main.cpp Functors.cpp)

if(${CMAKE_CXX_COMPILER_ID} STREQUAL GNU)
  target_compile_options(ddisasm PRIVATE -Wno-unused-parameter)
endif()

if(DDISASM_SOUFFLE_PROFILING)
  target_compile_definitions(ddisasm PRIVATE DDISASM_SOUFFLE_PROFILING)
endif()

configure_file("${CMAKE_CURRENT_SOURCE_DIR}/Version.h.in"
               "${CMAKE_BINARY_DIR}/include/Version.h" @ONLY)
target_include_directories(
  ddisasm PRIVATE $<BUILD_INTERFACE:${CMAKE_BINARY_DIR}/include>)
if(ehp_INCLUDE_DIR)
  target_include_directories(ddisasm PRIVATE ${ehp_INCLUDE_DIR})
endif()
if(CAPSTONE_INCLUDE_DIR)
  target_include_directories(ddisasm PRIVATE ${CAPSTONE_INCLUDE_DIR})
endif()
if(SOUFFLE_INCLUDE_DIR)
  target_include_directories(ddisasm SYSTEM PRIVATE ${SOUFFLE_INCLUDE_DIR})
endif()

target_compile_definitions(ddisasm PRIVATE __EMBEDDED_SOUFFLE__)
target_compile_definitions(ddisasm PRIVATE RAM_DOMAIN_SIZE=64)
target_compile_options(ddisasm PRIVATE ${OPENMP_FLAGS})

if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
  target_compile_definitions(ddisasm PRIVATE _CRT_SECURE_NO_WARNINGS)
  target_compile_definitions(ddisasm PRIVATE _CRT_NONSTDC_NO_WARNINGS)

  set_msvc_lief_options(ddisasm)
  set_common_msvc_options(ddisasm)
else()
  target_compile_options(ddisasm PRIVATE -O3)
  target_compile_options(ddisasm PRIVATE -Wall)
  target_compile_options(ddisasm PRIVATE -Wextra -Wpointer-arith)
  target_compile_options(ddisasm PRIVATE -Werror)
endif()

if(${GTIRB_USE_SYSTEM_BOOST} MATCHES "OFF")
  add_dependencies(ddisasm Boost)
endif()

if(DDISASM_STATIC_DRIVERS)
  if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
    # We do not want to statically link in the STL here, as MSVC is a bit
    # prickly about STL ABIs.
  else()
    target_link_libraries(ddisasm PRIVATE -static-libstdc++ -static-libgcc)
  endif()
endif()

if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
  target_link_libraries(ddisasm PRIVATE ${GENERATED_STATIC_LIB} scc_pass
                                        no_return_pass function_inference_pass)

  foreach(GENLIB ${GENERATED_STATIC_LIB})
    target_link_options(ddisasm PRIVATE
                        /WHOLEARCHIVE:${GENLIB}$<$<CONFIG:Debug>:d>)
  endforeach()

  target_link_options(
    ddisasm PRIVATE /WHOLEARCHIVE:no_return_pass$<$<CONFIG:Debug>:d>
    /WHOLEARCHIVE:function_inference_pass$<$<CONFIG:Debug>:d>)
else()
  if(APPLE)
    target_link_libraries(
      ddisasm PRIVATE scc_pass -Wl,-all_load ${GENERATED_STATIC_LIB}
                      no_return_pass function_inference_pass -Wl,-noall_load)
  else()
    target_link_libraries(
      ddisasm
      PRIVATE scc_pass -Wl,--whole-archive ${GENERATED_STATIC_LIB}
              no_return_pass function_inference_pass -Wl,--no-whole-archive)
  endif()
endif()

if(${CMAKE_CXX_COMPILER_ID} STREQUAL GNU)
  if(DDISASM_STATIC_DRIVERS)
    target_link_libraries(ddisasm PRIVATE -l:libgomp.a)
  else()
    target_link_libraries(ddisasm PRIVATE gomp)
  endif()
endif()

target_link_libraries(
  ddisasm
  PRIVATE ${GENERATED_STATIC_LIB}
          ddisasm_pipeline
          gtirb
          gtirb_pprinter
          gtirb_builder
          gtirb_decoder
          generic_pass
          disassembly_pass
          ${Boost_LIBRARIES}
          ${EXPERIMENTAL_LIB}
          ${LIBCPP_ABI}
          ${DDISASM_EXTRA_LIBS}
          ${LIBSTDCXX_FS})

if(DDISASM_ENABLE_TESTS)
  add_subdirectory(tests)
endif()

if(UNIX
   AND NOT CYGWIN
   AND ("${CMAKE_BUILD_TYPE}" STREQUAL "RelWithDebInfo" OR "${CMAKE_BUILD_TYPE}"
                                                           STREQUAL "Debug")
   AND ${DDISASM_STRIP_DEBUG_SYMBOLS})
  string(
    RANDOM
    LENGTH 32
    ALPHABET "abcdef0123456789" BUILD_ID)
  string(SUBSTRING "${BUILD_ID}" 0 2 BUILD_ID_PREFIX)
  string(SUBSTRING "${BUILD_ID}" 2 32 BUILD_ID_SUFFIX)
  target_link_libraries(ddisasm PRIVATE "-Wl,--build-id=0x${BUILD_ID}")
  add_custom_command(
    TARGET ddisasm
    POST_BUILD
    COMMAND objcopy --only-keep-debug $<TARGET_FILE:ddisasm>
            ${CMAKE_BINARY_DIR}/bin/${BUILD_ID_SUFFIX}.debug
    COMMAND objcopy --strip-debug $<TARGET_FILE:ddisasm>)
  install(
    FILES "${CMAKE_BINARY_DIR}/bin/${BUILD_ID_SUFFIX}.debug"
    COMPONENT debug-file
    DESTINATION "lib/debug/.build-id/${BUILD_ID_PREFIX}")
endif()

install(
  TARGETS ddisasm
  COMPONENT ddisasm
  DESTINATION bin)

if(BUILD_FUNINFER)
  # ===== souffle_funinfer =====

  add_executable(funinfer FunInfer.cpp)

  target_include_directories(
    funinfer PRIVATE $<BUILD_INTERFACE:${CMAKE_BINARY_DIR}/include>)

  if(SOUFFLE_INCLUDE_DIR)
    target_include_directories(funinfer PRIVATE ${SOUFFLE_INCLUDE_DIR})
  endif()

  if(${GTIRB_USE_SYSTEM_BOOST} MATCHES "OFF")
    add_dependencies(funinfer Boost)
  endif()

  if(DDISASM_STATIC_DRIVERS)
    if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
      # We do not want to statically link in the STL here, as MSVC is a bit
      # prickly about STL ABIs.
    else()
      target_link_libraries(funinfer PRIVATE -static-libstdc++ -static-libgcc)
    endif()
  endif()

  target_link_libraries(
    funinfer
    PRIVATE ddisasm_pipeline
            gtirb
            gtirb_decoder
            generic_pass
            scc_pass
            ${CAPSTONE}
            ${Boost_LIBRARIES}
            ${EXPERIMENTAL_LIB}
            ${LIBCPP_ABI})

  if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
    target_link_libraries(funinfer PRIVATE no_return_pass
                                           function_inference_pass)
    target_link_options(
      funinfer PRIVATE /WHOLEARCHIVE:no_return_pass$<$<CONFIG:Debug>:d>
      /WHOLEARCHIVE:function_inference_pass$<$<CONFIG:Debug>:d>)
  else()
    if(APPLE)
      target_link_libraries(
        funinfer PRIVATE -Wl,-all_load no_return_pass function_inference_pass
                         -Wl,-noall_load)
    else()
      target_link_libraries(
        funinfer PRIVATE -Wl,--whole-archive no_return_pass
                         function_inference_pass -Wl,--no-whole-archive)
    endif()
  endif()

  target_compile_options(funinfer PRIVATE ${OPENMP_FLAGS})

  if(${CMAKE_CXX_COMPILER_ID} STREQUAL MSVC)
    target_link_options(funinfer PRIVATE -NODEFAULTLIB:LIBCMTD)
    set_common_msvc_options(funinfer)
  else()
    target_compile_options(funinfer PRIVATE -O3)
    target_compile_options(funinfer PRIVATE -Wall)
    target_compile_options(funinfer PRIVATE -Wextra -Wpointer-arith)
    target_compile_options(funinfer PRIVATE -Werror)
  endif()

  if(${CMAKE_CXX_COMPILER_ID} STREQUAL GNU)
    if(DDISASM_STATIC_DRIVERS)
      target_link_libraries(funinfer PRIVATE -l:libgomp.a)
    else()
      target_link_libraries(funinfer PRIVATE gomp pthread)
    endif()
  endif()

  install(TARGETS funinfer DESTINATION bin)
endif()
