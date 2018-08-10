pkgname=buckup
pkgver=0.1a2
pkgrel=1
pkgdesc="Command line tool to create S3 buckups easily."
url="https://github.com/torchbox/buckup"
license=('BSD')
arch=('any')
depends=('python-boto3')
optdepends=('python-patchwork: Common deployment/sysadmin operations')
source=("https://github.com/torchbox/buckup/archive/v${pkgver}.tar.gz")

build() {
  cd "${srcdir}"/${pkgname}-${pkgver}
  python setup.py build
}

package() {
  cd "${srcdir}"/${pkgname}-${pkgver}
  python setup.py install -O1 --skip-build --root="${pkgdir}"

  install -Dm644 README.rst "${pkgdir}"/usr/share/doc/${pkgname}/README.rst
  install -Dm644 LICENSE "${pkgdir}"/usr/share/licenses/${pkgname}/LICENSE
}

