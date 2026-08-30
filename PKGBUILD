# Maintainer: Vaibhav Pandit <vaibhavpandit09@users.noreply.github.com>
pkgname=lumen-launcher
_pkgname=lumen
pkgver=0.5.0
pkgrel=1
pkgdesc="An agent-friendly command launcher for KDE Plasma"
arch=('any')
url="https://github.com/VaibhavPandit-09/lumen"
license=('MIT')
depends=('python' 'python-pyqt6')
makedepends=('python-setuptools' 'python-build' 'python-installer' 'python-wheel')
optdepends=('plasma-workspace: for KDE Plasma system actions and KRunner integration')
source=("$pkgname-$pkgver.tar.gz::https://github.com/VaibhavPandit-09/lumen/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$_pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$_pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 lumen.desktop "$pkgdir/usr/share/applications/lumen.desktop"
    if [ -f "lumen/assets/lumen.svg" ]; then
        install -Dm644 lumen/assets/lumen.svg "$pkgdir/usr/share/icons/hicolor/scalable/apps/lumen.svg"
    fi
}
