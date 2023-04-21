import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-openg2p-openg2p-program",
    description="Meta package for openg2p-openg2p-program Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-g2p_payment_phee>=15.0dev,<15.1dev',
        'odoo-addon-g2p_programs>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
