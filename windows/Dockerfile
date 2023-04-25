# escape=`

# this is assuming the docker file from gtirb-pprinter was run, may want to 
# combine this all into the ddisasm repo to make it smoother.
FROM gtirb:latest

#SHELL ["cmd", "/S", "/C"]
#install SOUFFLE dependencies 
RUN choco install sqlite -y --version 3.40.1 && `
    choco install winflexbison3 -y && `
    choco install gzip -y && `
    choco install python -y && `
    refreshenv

# RUN "C:\\BuildTools\\Common7\\Tools\\VsDevCmd.bat"
SHELL ["powershell.exe", "-NoLogo", "-ExecutionPolicy", "Bypass"]

RUN  git clone https://github.com/microsoft/vcpkg.git
RUN setx /M PATH $($env:PATH + ';C:\vcpkg'); setx /M VCPKG_ROOT "C:\vcpkg"; refreshenv
RUN  bootstrap-vcpkg.bat -disableMetrics
# The first time the command is run, it fails, second time, it works. I dunno....
RUN "try { & 'C:\vcpkg\vcpkg.exe' integrate install } catch { Write-Host 'Installation failed.' } ; exit 0"
RUN vcpkg.exe integrate install
RUN vcpkg.exe install sqlite3:x64-windows libffi:x64-windows zlib:x64-windows

SHELL ["cmd", "/S", "/C"]

# Build and install Souffle dependency, some of this stuff doesn't work well unless in a powershell env...
RUN refreshenv && cd wip &&git clone -b 2.4 https://github.com/souffle-lang/souffle && `
    cd souffle && `
    cmake -S . -B build -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake -DCMAKE_CXX_FLAGS=/bigobj -DSOUFFLE_DOMAIN_64BIT=ON `
        -DCMAKE_FILE_LIBRARY_PREFIXES=";lib" -DCMAKE_FIND_LIBRARY_SUFFIXES=".lib;.dll" -DCMAKE_INSTALL_PREFIX=C:/Souffle `
        -DSOUFFLE_USE_CURSES=OFF -DSOUFFLE_USE_ZLIB=ON -DSOUFFLE_USE_SQLITE=ON -DCMAKE_FIND_DEBUG_MODE=FALSE -DSOUFFLE_BASH_COMPLETION=OFF && `
    cmake --build build --config Release --target install && `
    xcopy build\src\*.dll C:\Souffle\bin && xcopy build\src\*.lib C:\Souffle\bin && `
    cd C:\wip && rmdir /s /q souffle
    
# Build and Install LIEF
RUN cd C:\wip && git clone -b 0.12.3 --depth 1 https://github.com/lief-project/LIEF.git &&`
    cd LIEF && cmake -DLIEF_PYTHON_API=OFF -DLIEF_USE_CRT_RELEASE=MT -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -B build -DCMAKE_INSTALL_PREFIX=C:/LIEF `
    -DLIEF_EXAMPLES=OFF -DLIEF_TESTS=OFF -DLIEF_DOC=OFF &&`
    cmake --build build --config Release --target install && cd .. && rmdir /s /q LIEF 
    
RUN setx PATH "%PATH%;C:\LIEF" && setx PATH "%PATH%;C:\Souffle"
    
RUN choco install -y vim 

# Build and Install LibEHP    
RUN cd C:\wip && git clone https://github.com/R2IDefense/libehp.git && cd libehp && `
    cmake -B build -DCMAKE_BUILD_TYPE=Release -DEHP_BUILD_SHARED_LIBS=OFF `
     -DCMAKE_INSTALL_PREFIX=C:/libehp -DCMAKE_CXX_FLAGS="/EHsc" && `
    cmake --build build --config Release --target install && cd .. && rmdir /s /q libehp && ` 
    setx PATH "%PATH%;C:\libehp" && refreshenv

# Install mcpp.exe, need to update CMakeLists to check for it and optionally run it....
RUN curl -SL --output mcpp.zip http://prdownloads.sourceforge.net/mcpp/mcpp-2.7.2-bin.zip?download && `
    "C:\Program Files\7-Zip\7z.exe" x mcpp.zip -bsp1 -aoa -y && del /s /q mcpp.zip && `
    setx /M PATH "%PATH%;C:\mcpp-2.7.2\bin;C:\Gtirb-pprinter;C:\Gtirb-pprinter\bin"

# Build and Install ddisasm 
RUN cd C:\wip && git clone https://github.com/R2IDefense/ddisasm.git && `
    cd ddisasm && `
    cmake -B build -DDDISASM_ARM_32=OFF -DDDISASM_ARM_64=OFF  -DBoost_USE_MULTITHREADED=ON -DBoost_USE_STATIC_LIBS=ON -DBoost_USE_STATIC_RUNTIME=ON`
     -DCMAKE_PREFIX_PATH=C:/LIEF/share/LIEF/cmake;C:/Souffle;C:/Capstone;C:/Gtirb-pprinter/lib;C:/Boost -DDDISASM_MIPS_32=OFF -DDDISASM_ENABLE_TESTS=OFF `
     -DDDISASM_STATIC_DRIVERS=ON -Dgtirb_pprinter_DIR=C:/Gtirb-pprinter -DCMAKE_CXX_FLAGS="-Dgtirb_layout_STATIC" -DDDISASM_BUILD_SHARED_LIBS=OFF -D_WIN32_WINNT=0x0601 `
     -DCMAKE_INSTALL_PREFIX=C:/DDisasm

RUN cd C:\wip\ddisasm && cmake --build build --config Release --target install 
